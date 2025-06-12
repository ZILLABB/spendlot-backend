"""
OCR processing tasks using Google Cloud Vision API.
"""
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from celery import current_task
from google.cloud import vision

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.services.receipt_service import ReceiptService
from app.services.categorization_service import CategorizationService

logger = get_logger(__name__)


@celery_app.task(bind=True)
def process_receipt_ocr(self, receipt_id: int):
    """Process receipt OCR using Google Cloud Vision API."""
    db = SessionLocal()
    try:
        receipt_service = ReceiptService(db)
        receipt = receipt_service.get(receipt_id)
        
        if not receipt:
            logger.error(f"Receipt {receipt_id} not found")
            return {"error": "Receipt not found"}
        
        if not receipt.file_path or not os.path.exists(receipt.file_path):
            logger.error(f"Receipt file not found: {receipt.file_path}")
            receipt_service.update_processing_status(
                receipt_id, "failed", "File not found"
            )
            return {"error": "File not found"}
        
        # Update status to processing
        receipt_service.update_processing_status(receipt_id, "processing")
        
        # Perform OCR
        ocr_result = perform_ocr(receipt.file_path)
        
        if not ocr_result:
            receipt_service.update_processing_status(
                receipt_id, "failed", "OCR processing failed"
            )
            return {"error": "OCR processing failed"}
        
        # Extract structured data
        extracted_data = extract_receipt_data(ocr_result["text"])
        
        # Update receipt with OCR results
        receipt_service.update_ocr_data(
            receipt_id,
            ocr_result["text"],
            ocr_result["confidence"],
            extracted_data
        )
        
        # Auto-categorize if possible
        if extracted_data.get("merchant_name"):
            categorization_service = CategorizationService(db)
            category = categorization_service.auto_categorize_receipt(receipt)
            if category:
                receipt_service.update(
                    db_obj=receipt,
                    obj_in={"category_id": category.id, "auto_categorized": True}
                )
        
        logger.info(f"Successfully processed OCR for receipt {receipt_id}")
        return {
            "receipt_id": receipt_id,
            "status": "completed",
            "extracted_data": extracted_data
        }
        
    except Exception as e:
        logger.error(f"Error processing OCR for receipt {receipt_id}: {str(e)}")
        receipt_service.update_processing_status(
            receipt_id, "failed", str(e)
        )
        return {"error": str(e)}
    finally:
        db.close()


def perform_ocr(file_path: str) -> Optional[Dict[str, Any]]:
    """Perform OCR on image using Google Cloud Vision API."""
    try:
        client = vision.ImageAnnotatorClient()
        
        with open(file_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            logger.error(f"Vision API error: {response.error.message}")
            return None
        
        texts = response.text_annotations
        if not texts:
            return {"text": "", "confidence": 0.0}
        
        # First annotation contains the full text
        full_text = texts[0].description
        
        # Calculate average confidence
        total_confidence = sum(
            text.confidence for text in texts[1:] if hasattr(text, 'confidence')
        )
        avg_confidence = total_confidence / len(texts[1:]) if len(texts) > 1 else 0.0
        
        return {
            "text": full_text,
            "confidence": avg_confidence * 100  # Convert to percentage
        }
        
    except Exception as e:
        logger.error(f"OCR processing error: {str(e)}")
        return None


def extract_receipt_data(text: str) -> Dict[str, Any]:
    """Extract structured data from OCR text."""
    extracted = {}
    
    # Extract merchant name (usually at the top)
    lines = text.split('\n')
    for i, line in enumerate(lines[:5]):  # Check first 5 lines
        line = line.strip()
        if len(line) > 3 and not re.match(r'^[\d\s\-\(\)]+$', line):
            extracted["merchant_name"] = line
            break
    
    # Extract total amount
    amount_patterns = [
        r'total[:\s]*\$?(\d+\.?\d*)',
        r'amount[:\s]*\$?(\d+\.?\d*)',
        r'\$(\d+\.\d{2})',
        r'(\d+\.\d{2})\s*$'
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                extracted["amount"] = Decimal(matches[-1])  # Take the last match
                break
            except:
                continue
    
    # Extract tax amount
    tax_patterns = [
        r'tax[:\s]*\$?(\d+\.?\d*)',
        r'hst[:\s]*\$?(\d+\.?\d*)',
        r'gst[:\s]*\$?(\d+\.?\d*)'
    ]
    
    for pattern in tax_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                extracted["tax_amount"] = Decimal(matches[0])
                break
            except:
                continue
    
    # Extract tip amount
    tip_patterns = [
        r'tip[:\s]*\$?(\d+\.?\d*)',
        r'gratuity[:\s]*\$?(\d+\.?\d*)'
    ]
    
    for pattern in tip_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                extracted["tip_amount"] = Decimal(matches[0])
                break
            except:
                continue
    
    # Extract date
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                date_str = matches[0]
                # Try to parse the date
                for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                    try:
                        extracted["transaction_date"] = datetime.strptime(date_str, fmt)
                        break
                    except:
                        continue
                break
            except:
                continue
    
    # Extract line items (simplified)
    line_items = []
    for line in lines:
        # Look for lines with item and price
        if re.search(r'\$\d+\.\d{2}', line) and len(line.strip()) > 5:
            parts = line.strip().split()
            if len(parts) >= 2:
                price_match = re.search(r'\$?(\d+\.\d{2})', line)
                if price_match:
                    description = line.replace(price_match.group(0), '').strip()
                    if description:
                        line_items.append({
                            "description": description,
                            "total_price": Decimal(price_match.group(1))
                        })
    
    if line_items:
        extracted["line_items"] = line_items
    
    return extracted


@celery_app.task
def process_pending_receipts():
    """Process all pending receipts."""
    db = SessionLocal()
    try:
        receipt_service = ReceiptService(db)
        pending_receipts = receipt_service.get_unprocessed(limit=10)
        
        for receipt in pending_receipts:
            process_receipt_ocr.delay(receipt.id)
        
        logger.info(f"Queued {len(pending_receipts)} receipts for OCR processing")
        return {"queued": len(pending_receipts)}
        
    except Exception as e:
        logger.error(f"Error processing pending receipts: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()
