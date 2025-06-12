# 📱 Frontend Integration Prompt for Spendlot Receipt Tracker

## 🎯 Project Overview

Build a React/React Native mobile application that integrates with the Spendlot Receipt Tracker backend API. This is a comprehensive receipt management system with OCR processing, bank account synchronization, and intelligent categorization.

## 🏗️ Backend API Base URL
- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## 📋 Required Features to Implement

### 🔐 1. Authentication System
- **User Registration** with email/password
- **Login/Logout** with JWT tokens
- **Password Reset** flow via email
- **Token Refresh** mechanism
- **Profile Management** (update user info)

### 🧾 2. Receipt Management
- **Photo Upload** with camera/gallery integration
- **Receipt List** with pagination and filtering
- **Receipt Details** view with OCR results
- **Manual Receipt Entry** for non-photo receipts
- **Receipt Editing** (merchant, amount, category, notes)
- **Receipt Verification** status tracking

### 💳 3. Transaction Management
- **Transaction List** with filtering and search
- **Manual Transaction Entry**
- **Transaction Categorization**
- **Transaction Details** view
- **Monthly/Weekly Summaries**

### 🏦 4. Bank Account Integration
- **Plaid Link** integration for bank connections
- **Account List** display
- **Transaction Sync** from banks
- **Account Management** (enable/disable sync)

### 🏷️ 5. Category Management
- **Category List** with hierarchical structure
- **Custom Category Creation**
- **Category Assignment** to transactions/receipts
- **Category Statistics** and insights

### 📊 6. Analytics Dashboard
- **Spending Summaries** by period
- **Category Breakdowns** with charts
- **Monthly Trends** visualization
- **Top Merchants** analysis
- **Budget vs Actual** comparisons

### 🔗 7. External Integrations
- **Gmail OAuth** for receipt email import
- **SMS Receipt Processing** status updates
- **Real-time Notifications** for processing updates

## 📚 API Endpoints Reference

### Authentication Endpoints
```
POST /auth/register          - Register new user
POST /auth/login             - User login
POST /auth/logout            - User logout
POST /auth/refresh           - Refresh access token
POST /auth/forgot-password   - Request password reset
POST /auth/reset-password    - Reset password with token
POST /auth/change-password   - Change password
GET  /users/me               - Get user profile
PUT  /users/me               - Update user profile
```

### Receipt Endpoints
```
GET    /receipts/            - List receipts (paginated)
POST   /receipts/upload      - Upload receipt image
GET    /receipts/{id}        - Get receipt details
PUT    /receipts/{id}        - Update receipt
DELETE /receipts/{id}        - Delete receipt
```

### Transaction Endpoints
```
GET  /transactions/                    - List transactions
POST /transactions/                    - Create transaction
GET  /transactions/{id}                - Get transaction
PUT  /transactions/{id}                - Update transaction
DELETE /transactions/{id}              - Delete transaction
GET  /transactions/summary/current-month - Monthly summary
```

### Category Endpoints
```
GET  /categories/        - List all categories
GET  /categories/tree    - Get category tree structure
POST /categories/        - Create category
PUT  /categories/{id}    - Update category
DELETE /categories/{id}  - Delete category
```

### Bank Account Endpoints
```
GET  /bank-accounts/                    - List bank accounts
POST /bank-accounts/plaid/link-token    - Create Plaid link token
POST /bank-accounts/plaid/exchange-token - Exchange Plaid token
POST /bank-accounts/{id}/sync           - Sync account transactions
```

### Analytics Endpoints
```
GET /analytics/spending-summary  - Spending analysis
GET /analytics/category-stats    - Category statistics
GET /analytics/monthly-trends    - Monthly spending trends
GET /analytics/receipt-stats     - Receipt processing stats
```

### External Service Endpoints
```
GET  /auth/gmail/authorize   - Get Gmail OAuth URL
GET  /auth/gmail/status      - Check Gmail connection
POST /auth/gmail/disconnect  - Disconnect Gmail
```

## 🔧 Required Dependencies

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "react-query": "^3.39.0",
    "@react-native-async-storage/async-storage": "^1.19.0",
    "react-plaid-link": "^3.4.0",
    "react-native-plaid-link-sdk": "^10.0.0",
    "react-native-image-picker": "^5.6.0",
    "react-dropzone": "^14.2.0"
  }
}
```

## 📝 TypeScript Interfaces

```typescript
// Core Data Models
interface User {
  id: number;
  email: string;
  full_name: string;
  phone_number?: string;
  timezone: string;
  currency: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

interface Receipt {
  id: number;
  merchant_name?: string;
  amount?: number;
  currency: string;
  transaction_date?: string;
  processing_status: 'pending' | 'completed' | 'failed';
  ocr_confidence?: number;
  is_verified: boolean;
  category_id?: number;
  notes?: string;
  file_path?: string;
  created_at: string;
}

interface Transaction {
  id: number;
  amount: number;
  currency: string;
  description?: string;
  transaction_date: string;
  transaction_type: 'credit' | 'debit';
  merchant_name?: string;
  category_id?: number;
  account_id?: number;
  is_pending: boolean;
  created_at: string;
}

interface Category {
  id: number;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: number;
  is_income: boolean;
  is_active: boolean;
}

interface BankAccount {
  id: number;
  account_name: string;
  account_type: string;
  institution_name: string;
  current_balance?: number;
  currency: string;
  is_active: boolean;
  last_sync_at?: string;
}

// API Response Types
interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: User;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

interface APIError {
  error: string;
  message: string;
  details?: any;
  status_code?: number;
}
```

## 🔐 Authentication Implementation

```typescript
// Token Management
const storeTokens = async (accessToken: string, refreshToken: string) => {
  await AsyncStorage.setItem('access_token', accessToken);
  await AsyncStorage.setItem('refresh_token', refreshToken);
};

const getAccessToken = async (): Promise<string | null> => {
  return await AsyncStorage.getItem('access_token');
};

// Axios Setup with Auto Token Refresh
axios.interceptors.request.use(async (config) => {
  const token = await getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          await storeTokens(response.data.access_token, response.data.refresh_token);
          // Retry original request
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
          return axios.request(error.config);
        } catch (refreshError) {
          // Refresh failed, logout user
          await logout();
        }
      }
    }
    return Promise.reject(error);
  }
);
```

## 📱 Key UI Components to Build

### 1. Authentication Screens
- **Login Screen** with email/password
- **Registration Screen** with form validation
- **Forgot Password Screen**
- **Profile Settings Screen**

### 2. Receipt Management
- **Receipt Camera Screen** with photo capture
- **Receipt List Screen** with search/filter
- **Receipt Detail Screen** with edit capabilities
- **Receipt Upload Progress** indicator

### 3. Transaction Management
- **Transaction List Screen** with filtering
- **Transaction Detail Screen**
- **Add Transaction Screen** (manual entry)
- **Transaction Categories** picker

### 4. Bank Integration
- **Bank Accounts List** screen
- **Plaid Link Integration** component
- **Account Sync Status** indicators

### 5. Analytics Dashboard
- **Spending Overview** with charts
- **Category Breakdown** pie charts
- **Monthly Trends** line graphs
- **Budget Tracking** progress bars

### 6. Settings & Integration
- **App Settings** screen
- **Gmail Integration** toggle
- **Notification Preferences**
- **Data Export** options

## 🔄 Real-time Features

### Receipt Processing Status
```typescript
// Poll for receipt processing completion
const pollReceiptStatus = async (receiptId: number) => {
  const maxAttempts = 30;
  let attempts = 0;
  
  const poll = async () => {
    const response = await axios.get(`/receipts/${receiptId}`);
    const receipt = response.data;
    
    if (receipt.processing_status === 'completed') {
      // Update UI with processed receipt
      return receipt;
    }
    
    if (receipt.processing_status === 'failed') {
      // Show error message
      throw new Error('Receipt processing failed');
    }
    
    // Continue polling
    attempts++;
    if (attempts < maxAttempts) {
      setTimeout(poll, 10000); // Poll every 10 seconds
    }
  };
  
  return poll();
};
```

## 🎨 UI/UX Requirements

### Design Guidelines
- **Material Design** (Android) / **Human Interface Guidelines** (iOS)
- **Dark/Light Mode** support
- **Responsive Design** for tablets
- **Accessibility** compliance (screen readers, etc.)

### Key User Flows
1. **Onboarding**: Registration → Bank Connection → First Receipt
2. **Daily Use**: Quick receipt capture → Auto-categorization → Review
3. **Analysis**: View spending → Drill down by category → Export data
4. **Management**: Edit transactions → Manage categories → Sync accounts

## 🚀 Getting Started

1. **Set up development environment** with React Native CLI
2. **Install required dependencies** from package.json
3. **Configure environment variables** for API endpoints
4. **Implement authentication flow** first
5. **Build core screens** (login, receipt list, upload)
6. **Add external integrations** (Plaid, camera)
7. **Implement analytics** and charts
8. **Add real-time features** and notifications
9. **Test thoroughly** on both platforms
10. **Prepare for production** deployment

## 📞 Backend Health Check

Test backend connectivity:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":...}

curl http://localhost:8000/api/v1/categories/
# Expected: 401 Unauthorized (requires auth)
```

## 🎯 Success Criteria

- ✅ Users can register and login securely
- ✅ Receipt photos are uploaded and processed via OCR
- ✅ Bank accounts can be connected via Plaid
- ✅ Transactions are automatically categorized
- ✅ Spending analytics are displayed with charts
- ✅ Real-time updates for processing status
- ✅ Offline capability for basic features
- ✅ Cross-platform compatibility (iOS/Android)

This backend provides a complete REST API with authentication, file uploads, external integrations, and real-time processing. Build a modern, intuitive mobile app that makes expense tracking effortless for users!
