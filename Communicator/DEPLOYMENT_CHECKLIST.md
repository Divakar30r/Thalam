# Deployment Checklist - Order Tracking Implementation

## Pre-Deployment Verification

### 1. Code Changes Complete ✅
- [x] Created `order_tracking_service.py` with OrderTrackingService
- [x] Updated `/initiate` endpoint with duplicate prevention
- [x] Updated `/followup` endpoint to populate notes_dict_arr
- [x] Added diagnostic endpoints `/tracking/status` and `/tracking/{order_req_id}`
- [x] Updated `grpc_client_service.py` to mark streams inactive
- [x] All files compile without errors

### 2. Documentation Created ✅
- [x] `IMPLEMENTATION_SUMMARY.md` - Complete technical overview
- [x] `ORDER_TRACKING_GUIDE.md` - Quick reference guide

## Deployment Steps

### Step 1: Stop Running Services
```powershell
# Stop processor service (Ctrl+C in terminal)
# Stop requestor service (Ctrl+C in terminal)
```

### Step 2: Verify Python Environment
```powershell
# Requestor
cd c:\Users\User\Documents\Myliving\dCent\Communicator\requestor
.\.venv\Scripts\activate
python --version  # Should be Python 3.12+

# Processor
cd c:\Users\User\Documents\Myliving\dCent\Communicator\processor
.\.venv\Scripts\activate
python --version  # Should be Python 3.12+
```

### Step 3: Start Processor Service
```powershell
cd c:\Users\User\Documents\Myliving\dCent\Communicator\processor
.\.venv\Scripts\activate
python main.py
```

**Expected Output**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8005 (Press CTRL+C to quit)
INFO:     gRPC Server started on port 50052
```

**Check for Issues**:
- ❌ Port binding errors
- ❌ Import errors
- ❌ Configuration errors

### Step 4: Start Requestor Service
```powershell
cd c:\Users\User\Documents\Myliving\dCent\Communicator\requestor
.\.venv\Scripts\activate
python main.py
```

**Expected Output**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8004 (Press CTRL+C to quit)
```

## Post-Deployment Testing

### Test 1: Health Check
```powershell
# Check requestor health
curl http://localhost:8004/api/v1/health

# Check processor health
curl http://localhost:8005/api/v1/health
```

**Expected**: Both return `{"status": "healthy"}`

### Test 2: Tracking Status (Initial)
```powershell
curl http://localhost:8004/api/v1/orders/tracking/status
```

**Expected**:
```json
{
  "total_orders": 0,
  "active_streams": 0,
  "tracked_order_ids": []
}
```

### Test 3: Initiate Order
```powershell
curl -X POST http://localhost:8004/api/v1/orders/initiate `
  -H "Content-Type: application/json" `
  -d '{
    "order_req_id": "TEST001",
    "session_id": "sess_test_001",
    "notification_type": "email"
  }'
```

**Expected**:
```json
{
  "success": true,
  "message": "Order initiated successfully",
  "order_req_id": "TEST001",
  "session_id": "sess_test_001"
}
```

**Check Logs**:
- Requestor: "Added order TEST001 to tracking list"
- Requestor: "Marked gRPC stream as active for order TEST001"
- Processor: "Request type: <class 'order_service_pb2.OrderStreamRequest'>" ✅

### Test 4: Verify Tracking Updated
```powershell
curl http://localhost:8004/api/v1/orders/tracking/status
```

**Expected**:
```json
{
  "total_orders": 1,
  "active_streams": 1,
  "tracked_order_ids": ["TEST001"]
}
```

### Test 5: Get Order Details
```powershell
curl http://localhost:8004/api/v1/orders/tracking/TEST001
```

**Expected**:
```json
{
  "order_req_id": "TEST001",
  "session": "sess_test_001",
  "notes_count": 0,
  "is_stream_active": true,
  "notes": []
}
```

### Test 6: Duplicate Prevention
```powershell
# Try to initiate same order again
curl -X POST http://localhost:8004/api/v1/orders/initiate `
  -H "Content-Type: application/json" `
  -d '{
    "order_req_id": "TEST001",
    "session_id": "sess_test_001",
    "notification_type": "email"
  }'
```

**Expected**:
```json
{
  "success": true,
  "message": "Order already being processed",
  "order_req_id": "TEST001",
  "session_id": "sess_test_001"
}
```

**Check Logs**:
- Requestor: "Order TEST001 already has active gRPC stream. Preventing duplicate stream."

### Test 7: Add Follow-Up
```powershell
curl -X POST http://localhost:8004/api/v1/orders/followup `
  -H "Content-Type: application/json" `
  -d '{
    "order_req_id": "TEST001",
    "audience": ["seller1", "seller2"],
    "message": {
      "urls": [],
      "message_type": "text",
      "message": "Please expedite this order"
    }
  }'
```

**Expected**:
```json
{
  "success": true,
  "message": "Follow-up processed successfully",
  "order_req_id": "TEST001"
}
```

**Check Logs**:
- Requestor: "Added follow-up note to order tracking for TEST001"

### Test 8: Verify Notes Added
```powershell
curl http://localhost:8004/api/v1/orders/tracking/TEST001
```

**Expected**:
```json
{
  "order_req_id": "TEST001",
  "session": "sess_test_001",
  "notes_count": 1,  # <-- Should be 1 now
  "is_stream_active": true,
  "notes": [
    {
      "follow_up_id": "...",
      "audience": ["seller1", "seller2"],
      "message_type": "text",
      "added_time": "2024-01-15T..."
    }
  ]
}
```

## Verification Criteria

### ✅ Success Indicators
1. Both services start without errors
2. Tracking status shows correct counts
3. Orders are added to tracking on /initiate
4. Duplicate orders are prevented
5. Follow-ups update notes_dict_arr
6. Processor logs show correct request type: `<class 'order_service_pb2.OrderStreamRequest'>`
7. No `grpc._cython.cygrpc._MessageReceiver` or `bytes` in processor logs
8. Streams marked inactive when complete

### ❌ Failure Indicators
1. Port binding errors (50052, 8004, 8005)
2. Import errors in new tracking service
3. Processor receives wrong request types
4. Duplicate prevention doesn't work
5. Notes don't appear in tracking
6. Stream state doesn't update

## Troubleshooting

### Issue: Port Already in Use
```
OSError: [WinError 10048] Only one usage of each socket address is normally permitted
```

**Solution**:
```powershell
# Find process using port
netstat -ano | findstr :8004
netstat -ano | findstr :8005
netstat -ano | findstr :50052

# Kill process
taskkill /PID <pid> /F
```

### Issue: Import Error for OrderTrackingService
```
ModuleNotFoundError: No module named 'requestor.app.services.order_tracking_service'
```

**Solution**:
- Verify file exists: `requestor/app/services/order_tracking_service.py`
- Check PYTHONPATH in `.venv/Scripts/activate.bat`
- Restart terminal and re-activate venv

### Issue: Processor Still Receiving Bytes
```
Request type: <class 'bytes'>
```

**Solution**:
- Verify interceptors.py changes applied
- Restart processor service (old code may be cached)
- Check no syntax errors in interceptors.py

### Issue: Duplicate Prevention Not Working
```
Multiple streams started for same order_req_id
```

**Solution**:
- Check `mark_stream_active()` is called in /initiate
- Verify `is_stream_active()` check happens before stream start
- Check order_tracking dependency injection works

## Rollback Plan

If critical issues occur:

### Option 1: Revert Order Tracking (Keep gRPC Fixes)
1. Remove order_tracking dependency from orders.py
2. Remove order_tracking from grpc_client_service.py
3. Keep interceptor fixes (critical for gRPC to work)

### Option 2: Full Rollback
1. Revert to commit before changes
2. Processor will still have gRPC type issues
3. Not recommended - loses interceptor fixes

## Performance Monitoring

### Metrics to Watch
- Memory usage (in-memory dict grows with orders)
- Active stream count vs total orders
- Response times for /initiate and /followup
- gRPC connection count

### Expected Behavior
- Memory: ~1-2 KB per OrderReqObj
- Stream ratio: Should match order count initially
- Response times: <100ms for tracking operations
- gRPC connections: 1 per active order

## Next Steps After Deployment

1. **Monitor for 24 hours**: Watch logs for errors
2. **Test with Real Orders**: Use actual order data
3. **Load Testing**: Test with multiple concurrent orders
4. **Add Metrics**: Implement Prometheus metrics for tracking
5. **Add Cleanup Job**: Periodically remove completed orders from tracking
6. **Add Persistence**: Consider Redis for tracking across restarts
7. **Address Port Conflict**: Resolve port 50051 issue

## Sign-Off

- [ ] All tests passed
- [ ] No errors in logs
- [ ] Duplicate prevention verified
- [ ] Notes tracking verified
- [ ] gRPC message types correct
- [ ] Documentation reviewed
- [ ] Rollback plan understood

**Deployed By**: _____________  
**Date**: _____________  
**Notes**: _____________
