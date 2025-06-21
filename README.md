PayMesh: Multi-Channel Secure Payment System

A production-ready, AI-powered payment platform that intelligently routes transactions across multiple channels while providing enterprise-grade fraud detection and security analytics.

See the full PayMesh workflow in action: Paymesh_demo.mp4

Key Features

Multi-Channel Routing
- Intelligent Fallback: Automatic channel selection (Internet → Bluetooth LE → SMS → Local Storage)
- Real-time Connectivity: Dynamic channel availability checking with DNS, HTTP, and ping validation
- Offline Resilience: Complete transaction capability without internet connectivity

AI-Powered Security Pipeline
- 4-Layer Protection: Phishing detection, fraud scoring, trust analysis, and SMS verification
- Neural Fraud Detection: PyTorch autoencoder for transaction anomaly detection
- SMS Phishing Prevention: SVM-based classification of malicious payment notifications
- Dynamic Trust Scoring: Real-time risk assessment based on user transaction patterns

Advanced Analytics
- Interactive Fraud Visualization: NetworkX-powered transaction risk graphs
- Real-time Security Metrics: Live dashboard with approval rates and risk statistics
- Comprehensive Audit Logging: Full transaction traceability for compliance

Execution Manual

Step-by-Step File Execution Order

Setup (Run Once)
1. python ledger.py - Initialize database
2. python train_phising_svm.py - Train phishing model
3. python training_autoencoder.py - Train fraud model

Main Demo
1. python test_multichannel.py - Test channel routing
2. python test_your_phishing_system.py - Test security pipeline
3. python paymesh_app.py - Launch full application
4. python scam_graph_mapper.py - Generate fraud analytics

Individual Component Testing
- python fraud_test.py - Fraud detection only
- python phishing_test.py - Phishing detection only  
- python ledger_test.py - Database operations


- python sync_server.py - Backend sync server

