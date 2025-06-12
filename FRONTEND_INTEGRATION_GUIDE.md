# 📱 Spendlot Frontend Integration Guide

**Complete API Integration Guide for React/React Native Applications**

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints Documentation](#api-endpoints-documentation)
3. [Authentication Flow](#authentication-flow)
4. [Data Models & TypeScript Interfaces](#data-models--typescript-interfaces)
5. [External Service Integration](#external-service-integration)
6. [Real-time Features](#real-time-features)
7. [Error Handling](#error-handling)
8. [Environment Configuration](#environment-configuration)
9. [Development Setup](#development-setup)
10. [Production Deployment](#production-deployment)
11. [Code Examples](#code-examples)

---

## 🚀 Quick Start

### Base API Configuration
```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';
const BASE_URL = `${API_BASE_URL}${API_VERSION}`;
```

### Essential Dependencies
```bash
npm install axios react-query @types/node
# For React Native
npm install @react-native-async-storage/async-storage
# For file uploads
npm install react-dropzone # Web only
```

---

## 📚 API Endpoints Documentation

### 🔐 Authentication Endpoints

#### **POST** `/auth/register`
Register a new user account.

**Request:**
```typescript
{
  email: string;
  password: string;
  full_name?: string;
  phone_number?: string;
}
```

**Response:**
```typescript
{
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}
```

#### **POST** `/auth/login`
Authenticate user and receive tokens.

**Request:**
```typescript
{
  email: string;
  password: string;
}
```

**Response:**
```typescript
{
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserProfile;
}
```

#### **POST** `/auth/refresh`
Refresh access token using refresh token.

**Request:**
```typescript
{
  refresh_token: string;
}
```

**Response:**
```typescript
{
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}
```

#### **POST** `/auth/logout`
Logout and invalidate tokens.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
{
  message: string;
}
```

#### **POST** `/auth/forgot-password`
Request password reset email.

**Request:**
```typescript
{
  email: string;
}
```

#### **POST** `/auth/reset-password`
Reset password with token.

**Request:**
```typescript
{
  token: string;
  new_password: string;
}
```

#### **POST** `/auth/change-password`
Change password for authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```typescript
{
  current_password: string;
  new_password: string;
}
```

### 👤 User Management

#### **GET** `/users/me`
Get current user profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
{
  id: number;
  email: string;
  full_name: string;
  phone_number?: string;
  profile_picture_url?: string;
  timezone: string;
  currency: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}
```

#### **PUT** `/users/me`
Update user profile.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```typescript
{
  full_name?: string;
  phone_number?: string;
  timezone?: string;
  currency?: string;
}
```

### 🧾 Receipt Management

#### **GET** `/receipts/`
Get user's receipts with pagination and filtering.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
```typescript
{
  page?: number;           // Default: 1
  size?: number;           // Default: 20, Max: 100
  merchant_name?: string;
  category_id?: number;
  date_from?: string;      // ISO date
  date_to?: string;        // ISO date
  min_amount?: number;
  max_amount?: number;
  processing_status?: 'pending' | 'completed' | 'failed';
  is_verified?: boolean;
}
```

**Response:**
```typescript
{
  items: Receipt[];
  total: number;
  page: number;
  size: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}
```

#### **POST** `/receipts/upload`
Upload receipt image for OCR processing.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request (FormData):**
```typescript
{
  file: File;              // Image file (JPG, PNG, PDF)
  merchant_name?: string;  // Optional pre-fill
  amount?: string;         // Optional pre-fill
  notes?: string;          // Optional notes
}
```

**Response:**
```typescript
{
  receipt_id: number;
  upload_id: string;
  processing_status: 'pending' | 'completed' | 'failed';
  message: string;
}
```

#### **GET** `/receipts/{id}`
Get specific receipt details.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
Receipt
```

#### **PUT** `/receipts/{id}`
Update receipt information.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```typescript
{
  merchant_name?: string;
  amount?: number;
  transaction_date?: string;
  category_id?: number;
  notes?: string;
  is_verified?: boolean;
}
```

#### **DELETE** `/receipts/{id}`
Delete a receipt.

**Headers:** `Authorization: Bearer <access_token>`

### 💳 Transaction Management

#### **GET** `/transactions/`
Get user's transactions with filtering.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
```typescript
{
  page?: number;
  size?: number;
  account_id?: number;
  category_id?: number;
  merchant_name?: string;
  transaction_type?: 'credit' | 'debit';
  date_from?: string;
  date_to?: string;
  min_amount?: number;
  max_amount?: number;
  is_pending?: boolean;
}
```

**Response:**
```typescript
PaginatedResponse<Transaction>
```

#### **POST** `/transactions/`
Create manual transaction.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```typescript
{
  amount: number;
  currency: string;
  description: string;
  transaction_date: string;
  transaction_type: 'credit' | 'debit';
  merchant_name?: string;
  category_id?: number;
  notes?: string;
}
```

#### **GET** `/transactions/summary/current-month`
Get current month transaction summary.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
{
  total_income: number;
  total_expenses: number;
  net_amount: number;
  transaction_count: number;
  avg_transaction_amount: number;
}
```

### 🏷️ Category Management

#### **GET** `/categories/`
Get all categories.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
Category[]
```

#### **GET** `/categories/tree`
Get categories in tree structure.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
{
  categories: CategoryWithChildren[];
}
```

#### **POST** `/categories/`
Create new category.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```typescript
{
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: number;
  is_income?: boolean;
}
```

### 🏦 Bank Account Management

#### **GET** `/bank-accounts/`
Get user's bank accounts.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
BankAccount[]
```

#### **POST** `/bank-accounts/plaid/link-token`
Create Plaid Link token for account connection.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
{
  link_token: string;
  expiration: string;
}
```

#### **POST** `/bank-accounts/plaid/exchange-token`
Exchange Plaid public token for access token.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```typescript
{
  public_token: string;
  institution_id: string;
  institution_name: string;
  account_ids: string[];
}
```

#### **POST** `/bank-accounts/{id}/sync`
Manually sync account transactions.

**Headers:** `Authorization: Bearer <access_token>`

### 📊 Analytics

#### **GET** `/analytics/spending-summary`
Get spending summary with analytics.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
```typescript
{
  period?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  start_date?: string;
  end_date?: string;
}
```

**Response:**
```typescript
{
  period: string;
  start_date: string;
  end_date: string;
  total_spent: number;
  total_income: number;
  transaction_count: number;
  top_categories: CategoryBreakdown[];
  daily_breakdown: DailySpending[];
}
```

#### **GET** `/analytics/monthly-trends`
Get monthly spending trends.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
```typescript
{
  months?: number; // Default: 12, Max: 24
}
```

### 🔗 External Service Integration

#### **GET** `/auth/gmail/authorize`
Get Gmail OAuth authorization URL.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
{
  authorization_url: string;
}
```

#### **GET** `/auth/gmail/status`
Check Gmail connection status.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```typescript
{
  connected: boolean;
}
```

#### **POST** `/auth/gmail/disconnect`
Disconnect Gmail integration.

**Headers:** `Authorization: Bearer <access_token>`

---

## 🔐 Authentication Flow

### Implementation Steps

#### 1. **Registration Flow**
```typescript
const register = async (userData: RegisterRequest): Promise<User> => {
  const response = await axios.post(`${BASE_URL}/auth/register`, userData);
  return response.data;
};
```

#### 2. **Login Flow**
```typescript
const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
  const response = await axios.post(`${BASE_URL}/auth/login`, credentials);

  // Store tokens securely
  await AsyncStorage.setItem('access_token', response.data.access_token);
  await AsyncStorage.setItem('refresh_token', response.data.refresh_token);

  return response.data;
};
```

#### 3. **Token Management**
```typescript
// Axios interceptor for automatic token attachment
axios.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Axios interceptor for automatic token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken
          });

          await AsyncStorage.setItem('access_token', response.data.access_token);
          await AsyncStorage.setItem('refresh_token', response.data.refresh_token);

          // Retry original request
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
          return axios.request(error.config);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          await logout();
          // Navigate to login screen
        }
      }
    }
    return Promise.reject(error);
  }
);
```

#### 4. **Logout Flow**
```typescript
const logout = async (): Promise<void> => {
  try {
    await axios.post(`${BASE_URL}/auth/logout`);
  } catch (error) {
    // Continue with logout even if API call fails
  } finally {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
    // Clear user state and navigate to login
  }
};
```

---

## 📝 Data Models & TypeScript Interfaces

### Core Interfaces

```typescript
// User Management
interface User {
  id: number;
  email: string;
  full_name: string;
  phone_number?: string;
  profile_picture_url?: string;
  timezone: string;
  currency: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  phone_number?: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: User;
}

// Receipt Management
interface Receipt {
  id: number;
  user_id: number;
  merchant_name?: string;
  amount?: number;
  currency: string;
  transaction_date?: string;
  receipt_number?: string;
  tax_amount?: number;
  tip_amount?: number;
  subtotal?: number;
  merchant_address?: string;
  merchant_phone?: string;
  latitude?: number;
  longitude?: number;
  original_filename?: string;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  ocr_text?: string;
  ocr_confidence?: number;
  processing_status: 'pending' | 'completed' | 'failed';
  processing_error?: string;
  line_items?: LineItem[];
  is_verified: boolean;
  is_duplicate: boolean;
  duplicate_of_id?: number;
  category_id?: number;
  auto_categorized: boolean;
  data_source_id: number;
  external_id?: string;
  extra_metadata?: Record<string, any>;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  category?: string;
}

interface ReceiptUploadRequest {
  file: File;
  merchant_name?: string;
  amount?: string;
  notes?: string;
}

interface ReceiptUploadResponse {
  receipt_id: number;
  upload_id: string;
  processing_status: 'pending' | 'completed' | 'failed';
  message: string;
}

// Transaction Management
interface Transaction {
  id: number;
  user_id: number;
  amount: number;
  currency: string;
  description?: string;
  transaction_date: string;
  transaction_type: 'credit' | 'debit';
  is_pending: boolean;
  merchant_name?: string;
  merchant_category?: string;
  account_id?: number;
  account_name?: string;
  plaid_transaction_id?: string;
  bank_transaction_id?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  category_id?: number;
  auto_categorized: boolean;
  subcategory?: string;
  receipt_id?: number;
  has_receipt: boolean;
  is_duplicate: boolean;
  duplicate_of_id?: number;
  data_source_id: number;
  processing_status: string;
  is_verified: boolean;
  extra_metadata?: Record<string, any>;
  tags?: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface TransactionCreateRequest {
  amount: number;
  currency: string;
  description: string;
  transaction_date: string;
  transaction_type: 'credit' | 'debit';
  merchant_name?: string;
  category_id?: number;
  notes?: string;
}

// Category Management
interface Category {
  id: number;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: number;
  level: number;
  is_system: boolean;
  is_active: boolean;
  is_income: boolean;
  keywords?: string;
  created_at: string;
  updated_at: string;
}

interface CategoryWithChildren extends Category {
  children?: Category[];
}

interface CategoryCreateRequest {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: number;
  is_income?: boolean;
}

// Bank Account Management
interface BankAccount {
  id: number;
  user_id: number;
  account_name: string;
  account_type: string;
  account_subtype?: string;
  institution_name: string;
  institution_id?: string;
  plaid_account_id?: string;
  plaid_item_id?: number;
  is_active: boolean;
  is_primary: boolean;
  current_balance?: number;
  available_balance?: number;
  currency: string;
  last_balance_update?: string;
  auto_sync: boolean;
  last_sync_at?: string;
  sync_status: string;
  sync_error?: string;
  extra_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Analytics
interface SpendingSummary {
  period: string;
  start_date: string;
  end_date: string;
  total_spent: number;
  total_income: number;
  transaction_count: number;
  top_categories: CategoryBreakdown[];
  daily_breakdown: DailySpending[];
}

interface CategoryBreakdown {
  category: Category;
  amount: number;
  percentage: number;
  transaction_count: number;
}

interface DailySpending {
  date: string;
  amount: number;
  transaction_count: number;
}

interface MonthlyTrend {
  year: number;
  month: number;
  total_spent: number;
  transaction_count: number;
  month_name: string;
}

// Pagination
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// API Error Response
interface APIError {
  error: string;
  message: string;
  details?: Record<string, any>;
  status_code?: number;
  type?: string;
}
```

---

## 🔗 External Service Integration

### Plaid Link Integration

#### 1. **Install Plaid Link**
```bash
# For React
npm install react-plaid-link

# For React Native
npm install react-native-plaid-link-sdk
```

#### 2. **Plaid Link Component (React)**
```typescript
import { usePlaidLink } from 'react-plaid-link';

interface PlaidLinkProps {
  onSuccess: (publicToken: string, metadata: any) => void;
  onExit?: (error: any, metadata: any) => void;
}

const PlaidLinkComponent: React.FC<PlaidLinkProps> = ({ onSuccess, onExit }) => {
  const [linkToken, setLinkToken] = useState<string | null>(null);

  useEffect(() => {
    const createLinkToken = async () => {
      try {
        const response = await axios.post(`${BASE_URL}/bank-accounts/plaid/link-token`);
        setLinkToken(response.data.link_token);
      } catch (error) {
        console.error('Error creating link token:', error);
      }
    };

    createLinkToken();
  }, []);

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: (publicToken, metadata) => {
      onSuccess(publicToken, metadata);
    },
    onExit: (error, metadata) => {
      onExit?.(error, metadata);
    },
  });

  return (
    <button onClick={() => open()} disabled={!ready}>
      Connect Bank Account
    </button>
  );
};
```

#### 3. **Handle Plaid Success**
```typescript
const handlePlaidSuccess = async (publicToken: string, metadata: any) => {
  try {
    const response = await axios.post(`${BASE_URL}/bank-accounts/plaid/exchange-token`, {
      public_token: publicToken,
      institution_id: metadata.institution.institution_id,
      institution_name: metadata.institution.name,
      account_ids: metadata.accounts.map((account: any) => account.id),
    });

    // Refresh bank accounts list
    await refetchBankAccounts();

    // Show success message
    alert('Bank account connected successfully!');
  } catch (error) {
    console.error('Error exchanging token:', error);
    alert('Failed to connect bank account. Please try again.');
  }
};
```

### Gmail OAuth Integration

#### 1. **Gmail OAuth Flow**
```typescript
const connectGmail = async () => {
  try {
    // Get authorization URL
    const response = await axios.get(`${BASE_URL}/auth/gmail/authorize`);
    const authUrl = response.data.authorization_url;

    // Open authorization URL in browser/webview
    // For React: window.open(authUrl)
    // For React Native: use Linking.openURL(authUrl) or in-app browser

    window.open(authUrl, '_blank');
  } catch (error) {
    console.error('Error starting Gmail OAuth:', error);
  }
};

const checkGmailStatus = async () => {
  try {
    const response = await axios.get(`${BASE_URL}/auth/gmail/status`);
    return response.data.connected;
  } catch (error) {
    console.error('Error checking Gmail status:', error);
    return false;
  }
};

const disconnectGmail = async () => {
  try {
    await axios.post(`${BASE_URL}/auth/gmail/disconnect`);
    // Update UI to reflect disconnection
  } catch (error) {
    console.error('Error disconnecting Gmail:', error);
  }
};
```

### File Upload Implementation

#### 1. **Receipt Upload (React)**
```typescript
import { useDropzone } from 'react-dropzone';

const ReceiptUpload: React.FC = () => {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${BASE_URL}/receipts/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          // Update progress bar
        },
      });

      // Handle successful upload
      console.log('Upload successful:', response.data);

      // Poll for processing completion
      pollReceiptProcessing(response.data.receipt_id);

    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'application/pdf': ['.pdf']
    },
    maxSize: 10485760, // 10MB
    multiple: false
  });

  return (
    <div {...getRootProps()} className="dropzone">
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop the receipt here...</p>
      ) : (
        <p>Drag & drop a receipt, or click to select</p>
      )}
      {uploading && <p>Uploading...</p>}
    </div>
  );
};
```

#### 2. **Receipt Upload (React Native)**
```typescript
import { launchImageLibrary, launchCamera } from 'react-native-image-picker';

const uploadReceipt = async (imageUri: string) => {
  const formData = new FormData();
  formData.append('file', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'receipt.jpg',
  } as any);

  try {
    const response = await axios.post(`${BASE_URL}/receipts/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
};

const selectImage = () => {
  launchImageLibrary(
    {
      mediaType: 'photo',
      quality: 0.8,
      maxWidth: 1024,
      maxHeight: 1024,
    },
    (response) => {
      if (response.assets && response.assets[0]) {
        uploadReceipt(response.assets[0].uri!);
      }
    }
  );
};
```

---

## ⚡ Real-time Features

### Polling for Receipt Processing

```typescript
const pollReceiptProcessing = async (receiptId: number) => {
  const maxAttempts = 30; // 5 minutes with 10-second intervals
  let attempts = 0;

  const poll = async (): Promise<void> => {
    try {
      const response = await axios.get(`${BASE_URL}/receipts/${receiptId}`);
      const receipt = response.data;

      if (receipt.processing_status === 'completed') {
        // Processing complete, update UI
        onReceiptProcessed(receipt);
        return;
      }

      if (receipt.processing_status === 'failed') {
        // Processing failed, show error
        onReceiptProcessingFailed(receipt);
        return;
      }

      // Still processing, continue polling
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(poll, 10000); // Poll every 10 seconds
      } else {
        // Timeout, stop polling
        onReceiptProcessingTimeout(receiptId);
      }
    } catch (error) {
      console.error('Error polling receipt status:', error);
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(poll, 10000);
      }
    }
  };

  poll();
};
```

### WebSocket Implementation (Optional)

```typescript
// WebSocket connection for real-time updates
class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(token: string) {
    const wsUrl = `ws://localhost:8000/ws?token=${token}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect(token);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'receipt_processed':
        // Update receipt in state
        break;
      case 'transaction_synced':
        // Update transactions list
        break;
      case 'bank_sync_completed':
        // Refresh bank accounts
        break;
    }
  }

  private reconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(token), 5000);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

---

## ❌ Error Handling

### Error Response Format

All API errors follow this consistent format:

```typescript
interface APIError {
  error: string;           // Error type
  message: string;         // Human-readable message
  details?: any;           // Additional error details
  status_code?: number;    // HTTP status code
  type?: string;           // Error category
}
```

### Common Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (duplicate) |
| 422 | Validation Error | Input validation failed |
| 429 | Rate Limited | Too many requests |
| 500 | Internal Error | Server error |
| 502 | Service Error | External service error |
| 503 | Service Unavailable | Service temporarily down |

### Error Handling Implementation

```typescript
// Global error handler
const handleAPIError = (error: any): string => {
  if (error.response) {
    const apiError: APIError = error.response.data;

    switch (error.response.status) {
      case 400:
        return apiError.message || 'Invalid request. Please check your input.';
      case 401:
        // Handle authentication error
        logout();
        return 'Session expired. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return apiError.message || 'This item already exists.';
      case 422:
        // Handle validation errors
        if (apiError.details) {
          return formatValidationErrors(apiError.details);
        }
        return apiError.message || 'Please check your input and try again.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'An unexpected error occurred. Please try again later.';
      case 502:
        return 'External service error. Please try again later.';
      case 503:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        return apiError.message || 'An error occurred. Please try again.';
    }
  } else if (error.request) {
    // Network error
    return 'Network error. Please check your connection and try again.';
  } else {
    // Other error
    return 'An unexpected error occurred.';
  }
};

// Format validation errors
const formatValidationErrors = (details: any): string => {
  if (Array.isArray(details)) {
    return details.map(error => error.msg || error.message).join(', ');
  }
  return 'Validation error occurred.';
};

// Axios error interceptor
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMessage = handleAPIError(error);

    // Show error to user (toast, alert, etc.)
    showErrorMessage(errorMessage);

    return Promise.reject(error);
  }
);
```

### React Query Error Handling

```typescript
import { useQuery, useMutation } from 'react-query';

// Query with error handling
const useReceipts = (filters: ReceiptFilters) => {
  return useQuery(
    ['receipts', filters],
    () => fetchReceipts(filters),
    {
      onError: (error) => {
        const message = handleAPIError(error);
        showErrorMessage(message);
      },
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error.response?.status >= 400 && error.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
    }
  );
};

// Mutation with error handling
const useUploadReceipt = () => {
  return useMutation(uploadReceipt, {
    onError: (error) => {
      const message = handleAPIError(error);
      showErrorMessage(message);
    },
    onSuccess: (data) => {
      showSuccessMessage('Receipt uploaded successfully!');
      // Invalidate and refetch receipts
      queryClient.invalidateQueries('receipts');
    },
  });
};
```

---

## ⚙️ Environment Configuration

### Environment Variables

Create a `.env` file in your frontend project:

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_VERSION=v1

# Plaid Configuration
REACT_APP_PLAID_ENV=sandbox
REACT_APP_PLAID_PUBLIC_KEY=your_plaid_public_key

# Google OAuth (for Gmail)
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id

# App Configuration
REACT_APP_APP_NAME=Spendlot
REACT_APP_VERSION=1.0.0

# Feature Flags
REACT_APP_ENABLE_GMAIL_INTEGRATION=true
REACT_APP_ENABLE_BANK_SYNC=true
REACT_APP_ENABLE_SMS_RECEIPTS=true

# Development
REACT_APP_DEBUG=true
REACT_APP_LOG_LEVEL=debug
```

### Configuration Service

```typescript
interface AppConfig {
  apiUrl: string;
  apiVersion: string;
  plaidEnv: 'sandbox' | 'development' | 'production';
  plaidPublicKey: string;
  googleClientId: string;
  appName: string;
  version: string;
  features: {
    gmailIntegration: boolean;
    bankSync: boolean;
    smsReceipts: boolean;
  };
  debug: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

const config: AppConfig = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  apiVersion: process.env.REACT_APP_API_VERSION || 'v1',
  plaidEnv: (process.env.REACT_APP_PLAID_ENV as any) || 'sandbox',
  plaidPublicKey: process.env.REACT_APP_PLAID_PUBLIC_KEY || '',
  googleClientId: process.env.REACT_APP_GOOGLE_CLIENT_ID || '',
  appName: process.env.REACT_APP_APP_NAME || 'Spendlot',
  version: process.env.REACT_APP_VERSION || '1.0.0',
  features: {
    gmailIntegration: process.env.REACT_APP_ENABLE_GMAIL_INTEGRATION === 'true',
    bankSync: process.env.REACT_APP_ENABLE_BANK_SYNC === 'true',
    smsReceipts: process.env.REACT_APP_ENABLE_SMS_RECEIPTS === 'true',
  },
  debug: process.env.REACT_APP_DEBUG === 'true',
  logLevel: (process.env.REACT_APP_LOG_LEVEL as any) || 'info',
};

export default config;
```

---

## 🛠️ Development Setup

### Prerequisites

```bash
# Node.js (v16 or higher)
node --version

# npm or yarn
npm --version
```

### Step-by-Step Setup

#### 1. **Clone and Install**
```bash
# Clone your frontend repository
git clone <your-frontend-repo>
cd spendlot-frontend

# Install dependencies
npm install
```

#### 2. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

#### 3. **Start Backend Services**
```bash
# In the backend directory
cd ../spendlot-backend
docker-compose up -d
```

#### 4. **Verify Backend Connection**
```bash
# Test API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":...}
```

#### 5. **Start Frontend Development Server**
```bash
# Back to frontend directory
cd ../spendlot-frontend

# Start development server
npm start

# For React Native
npx react-native run-ios
# or
npx react-native run-android
```

### Development Tools

#### API Client Setup
```typescript
// src/services/api.ts
import axios from 'axios';
import config from '../config';

const api = axios.create({
  baseURL: `${config.apiUrl}/api/${config.apiVersion}`,
  timeout: 10000,
});

// Add request interceptor for authentication
api.interceptors.request.use(async (config) => {
  const token = await getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    handleAPIError(error);
    return Promise.reject(error);
  }
);

export default api;
```

#### React Query Setup
```typescript
// src/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

export const QueryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
    {config.debug && <ReactQueryDevtools initialIsOpen={false} />}
  </QueryClientProvider>
);
```

### Testing Setup

```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

```typescript
// src/test-utils.tsx
import { render } from '@testing-library/react';
import { QueryProvider } from './providers/QueryProvider';

const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <QueryProvider>
      {children}
    </QueryProvider>
  );
};

const customRender = (ui: React.ReactElement, options = {}) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```
