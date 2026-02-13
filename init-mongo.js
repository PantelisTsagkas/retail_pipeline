// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

// Switch to retail database
db = db.getSiblingDB('retail_db');

// Create a user for the retail_db database (optional, since admin user can access all)
db.createUser({
  user: 'retail_user',
  pwd: 'retail_password',
  roles: [
    {
      role: 'readWrite',
      db: 'retail_db'
    }
  ]
});

// Create transactions collection with schema validation
db.createCollection('transactions', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["InvoiceNo", "StockCode", "Description", "Quantity", "UnitPrice", "Country"],
      properties: {
        InvoiceNo: {
          bsonType: ["int", "double", "string"],
          description: "Invoice number - required and must be number"
        },
        StockCode: {
          bsonType: "string",
          description: "Stock code - required and must be string"
        },
        Description: {
          bsonType: "string",
          description: "Item description - required and must be string"
        },
        Quantity: {
          bsonType: ["int", "double"],
          description: "Quantity - required and must be number"
        },
        UnitPrice: {
          bsonType: ["int", "double"],
          description: "Unit price - required and must be number"
        },
        CustomerID: {
          bsonType: ["int", "double", "null"],
          description: "Customer ID - can be null or number"
        },
        Country: {
          bsonType: "string",
          description: "Country - required and must be string"
        },
        InvoiceDate: {
          bsonType: "string",
          description: "Invoice date as string"
        },
        TotalAmount: {
          bsonType: ["int", "double"],
          description: "Calculated total amount"
        }
      }
    }
  }
});

// Create indexes for better performance
db.transactions.createIndex({ "InvoiceNo": 1 });
db.transactions.createIndex({ "CustomerID": 1 });
db.transactions.createIndex({ "Country": 1 });
db.transactions.createIndex({ "InvoiceDate": 1 });
db.transactions.createIndex({ "TotalAmount": -1 });

// Create compound index for common queries
db.transactions.createIndex({ 
  "Country": 1, 
  "InvoiceDate": 1, 
  "TotalAmount": -1 
});

print('✅ Database initialization completed successfully');
print('📊 Created retail_db database with transactions collection');
print('👤 Created retail_user with readWrite permissions');
print('🔍 Created performance indexes');
print('✔️ Schema validation enabled');