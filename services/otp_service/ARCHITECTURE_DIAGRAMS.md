# OTP Service Architecture & Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend / Client                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway (8000)                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │    Auth      │ │   Payment    │ │   Tuition    │
     │  Service     │ │  Service     │ │   Service    │
     │   (8001)     │ │   (8003)     │ │   (8005)     │
     └──────────────┘ └──────┬───────┘ └──────────────┘
                             │
                             ▼
                    ┌──────────────┐
                    │     OTP      │◄──────────┐
                    │   Service    │           │
                    │   (8002)     │           │
                    └──────┬───────┘           │
                           │                   │
                           ▼                   │
                    ┌──────────────┐           │
                    │    Redis     │           │
                    │   (6379)     │           │
                    └──────────────┘           │
                           ▲                   │
                           │                   │
                           └───────────────────┘
                        (Store/Retrieve OTP)
```

## OTP Service Internal Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         OTP Service (FastAPI)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API Layer (Routes)                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ Request  │ │  Verify  │ │  Resend  │ │  Status  │  │   │
│  │  │   OTP    │ │   OTP    │ │   OTP    │ │   & Del  │  │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │   │
│  └───────┼────────────┼────────────┼────────────┼─────────┘   │
│          │            │            │            │               │
│  ┌───────▼────────────▼────────────▼────────────▼─────────┐   │
│  │                  Business Logic Layer                   │   │
│  │                   (OTP Service Class)                   │   │
│  │                                                          │   │
│  │  • generate_otp()      • get_otp_data()                │   │
│  │  • verify_otp()        • get_remaining_time()          │   │
│  │  • resend_otp()        • get_attempts_remaining()      │   │
│  │  • delete_otp()        • is_payment_locked()           │   │
│  └───────┬──────────────────────────────────────────┬─────┘   │
│          │                                           │          │
│  ┌───────▼───────────────────────────────────────────▼─────┐  │
│  │              Data Access Layer (Redis Client)           │  │
│  │                                                          │  │
│  │  • set()    • get()     • exists()   • ttl()           │  │
│  │  • delete() • incr()    • expire()                     │  │
│  └───────┬──────────────────────────────────────────┬─────┘  │
│          │                                           │          │
└──────────┼───────────────────────────────────────────┼─────────┘
           │                                           │
           ▼                                           ▼
    ┌─────────────────────────────────────────────────────┐
    │                   Redis Database                     │
    │                                                      │
    │  Keys:                                              │
    │  • otp:{payment_id}          [TTL: 60s]            │
    │  • otp_attempts:{payment_id} [TTL: 300s]           │
    │  • otp_lock:{payment_id}     [TTL: 300s]           │
    └─────────────────────────────────────────────────────┘
```

## Complete Payment Flow with OTP

```
┌────────┐                                                    ┌────────┐
│  User  │                                                    │ System │
└───┬────┘                                                    └───┬────┘
    │                                                             │
    │ 1. Create Payment Request                                  │
    ├────────────────────────────────────────────────────────────►
    │                                                             │
    │                          2. Validate Payment Data          │
    │                                    ┌────────────────────────┤
    │                                    │ Payment Service        │
    │                                    └────────────────────────┤
    │                                                             │
    │                          3. Request OTP                     │
    │                                    ┌────────────────────────┤
    │                                    │ OTP Service            │
    │                                    │ - Generate 6-digit OTP │
    │                                    │ - Store in Redis (60s) │
    │                                    └────────────────────────┤
    │                                                             │
    │◄────────────────────────────────────────────────────────────┤
    │ 4. Payment ID + OTP Request Sent                            │
    │    (OTP sent to email/SMS)                                  │
    │                                                             │
    │ 5. User receives OTP: "123456"                              │
    │    Countdown: 60 seconds                                    │
    │                                                             │
    │ 6. Submit OTP Code                                          │
    ├────────────────────────────────────────────────────────────►
    │                                                             │
    │                          7. Verify OTP                      │
    │                                    ┌────────────────────────┤
    │                                    │ OTP Service            │
    │                                    │ - Check code match     │
    │                                    │ - Track attempts       │
    │                                    └────────────────────────┤
    │                                                             │
    │────────── SCENARIO A: OTP CORRECT ──────────►               │
    │                                                             │
    │                          8a. OTP Verified ✓                 │
    │                                    ┌────────────────────────┤
    │                                    │ - Delete OTP data      │
    │                                    │ - Create Transaction   │
    │                                    └────────────────────────┤
    │                                                             │
    │◄────────────────────────────────────────────────────────────┤
    │ 9a. Payment Success + Transaction ID                        │
    │                                                             │
    │────────── SCENARIO B: OTP EXPIRED ───────────►              │
    │                                                             │
    │◄────────────────────────────────────────────────────────────┤
    │ 8b. OTP Expired ⏱                                           │
    │                                                             │
    │ 9b. Click "Resend OTP"                                      │
    ├────────────────────────────────────────────────────────────►
    │                                                             │
    │                          10b. Generate New OTP              │
    │                                    ┌────────────────────────┤
    │                                    │ - Delete old OTP       │
    │                                    │ - Create new OTP (60s) │
    │                                    └────────────────────────┤
    │                                                             │
    │◄────────────────────────────────────────────────────────────┤
    │ 11b. New OTP sent                                           │
    │     (Continue from step 5)                                  │
    │                                                             │
    │────────── SCENARIO C: WRONG OTP ─────────────►              │
    │                                                             │
    │◄────────────────────────────────────────────────────────────┤
    │ 8c. Wrong OTP ✗ (Attempt 1/3)                               │
    │     "2 attempts remaining"                                  │
    │                                                             │
    │ 9c. Try again (wrong OTP)                                   │
    ├────────────────────────────────────────────────────────────►
    │                                                             │
    │◄────────────────────────────────────────────────────────────┤
    │ 10c. Wrong OTP ✗ (Attempt 2/3)                              │
    │      "1 attempt remaining"                                  │
    │                                                             │
    │ 11c. Try again (wrong OTP)                                  │
    ├────────────────────────────────────────────────────────────►
    │                                                             │
    │                          12c. Max Attempts Reached 🔒       │
    │                                    ┌────────────────────────┤
    │                                    │ - Set payment lock     │
    │                                    │ - Delete OTP           │
    │                                    │ - Cancel payment       │
    │                                    └────────────────────────┤
    │                                                             │
    │◄────────────────────────────────────────────────────────────┤
    │ 13c. Payment Locked (5 min)                                 │
    │      "Too many failed attempts"                             │
    │      Must create new payment                                │
    │                                                             │
└────┘                                                        └────┘
```

## Redis Data Lifecycle

```
TIME (seconds)    STATE                                   REDIS KEYS
═══════════════════════════════════════════════════════════════════════

T=0              OTP Request
                 ├─ Generate code: "123456"             otp:{payment_id}
                 ├─ Store in Redis                      otp_attempts:{payment_id}
                 └─ Set TTL: 60s                        

T=10             User receives OTP
                 └─ TTL remaining: 50s                  [Keys exist]

T=30             User submits WRONG OTP (1st)
                 ├─ Verify failed
                 └─ Increment attempts: 1               otp_attempts = "1"

T=40             User submits WRONG OTP (2nd)
                 ├─ Verify failed
                 └─ Increment attempts: 2               otp_attempts = "2"

T=50             User submits WRONG OTP (3rd)
                 ├─ Max attempts reached
                 ├─ Create lock
                 ├─ Delete OTP data                     otp_lock:{payment_id}
                 └─ Cancel payment                      [otp deleted]
                                                        [otp_attempts deleted]

T=350            Lock expires
                 └─ Auto-delete lock                    [all keys deleted]

─────────────────────────────────────────────────────────────────────

ALTERNATIVE: SUCCESS PATH

T=0              OTP Request
                 └─ Store OTP (60s TTL)                 otp:{payment_id}
                                                        otp_attempts:{payment_id}

T=25             User submits CORRECT OTP
                 ├─ Verify success
                 ├─ Delete all OTP data                 [all keys deleted]
                 └─ Create transaction                  

─────────────────────────────────────────────────────────────────────

ALTERNATIVE: EXPIRATION PATH

T=0              OTP Request
                 └─ Store OTP (60s TTL)                 otp:{payment_id}

T=60             OTP Expires
                 └─ Redis auto-deletes                  [otp deleted]
                                                        [otp_attempts exists]

T=65             User clicks "Resend"
                 ├─ Check for existing OTP data
                 ├─ Not found (expired)
                 └─ Generate new OTP                    otp:{payment_id} (new)
```

## API Endpoint Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     POST /api/otp/request                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: {payment_id, tuition_id, user_id, amount, email}   │
│                                                              │
│  Process:                                                    │
│  1. Check if payment is locked ──────► return 423 if locked│
│  2. Generate 6-digit OTP code                               │
│  3. Create OTPData object                                   │
│  4. Store in Redis (key: otp:{payment_id}, TTL: 60s)       │
│  5. Initialize attempts counter (key: otp_attempts:{...})  │
│                                                              │
│  Output: {success, message, expires_in: 60, attempts: 3}   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     POST /api/otp/verify                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: {payment_id, otp_code}                              │
│                                                              │
│  Process:                                                    │
│  1. Check if payment is locked ──────► return locked status │
│  2. Get OTP data from Redis ─────────► return 404 if none  │
│  3. Get current attempts count                              │
│  4. Compare otp_code with stored code                       │
│                                                              │
│     ┌─ IF MATCH:                                            │
│     │  • Delete OTP data                                    │
│     │  • Delete attempts counter                            │
│     └─► return {verified: true}                             │
│                                                              │
│     ┌─ IF NO MATCH:                                         │
│     │  • Increment attempts                                 │
│     │  • Check if attempts >= 3                             │
│     │    ┌─ IF YES:                                         │
│     │    │  • Set lock (5 min)                              │
│     │    │  • Delete OTP data                               │
│     │    └─► return {locked: true, attempts: 0}             │
│     │    ┌─ IF NO:                                          │
│     │    └─► return {verified: false, attempts_remaining}   │
│     └─                                                       │
│                                                              │
│  Output: {success, verified, locked, attempts_remaining}    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     POST /api/otp/resend                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: {payment_id}                                         │
│                                                              │
│  Process:                                                    │
│  1. Check if payment is locked ──────► return 423 if locked│
│  2. Get existing OTP data ───────────► return 404 if none  │
│  3. Extract payment context (tuition_id, user_id, etc)     │
│  4. Delete old OTP                                          │
│  5. Generate new OTP (same as /request)                     │
│  6. Store new OTP (60s TTL)                                 │
│                                                              │
│  Output: {success, message, expires_in: 60, attempts: 3}   │
└─────────────────────────────────────────────────────────────┘
```

## State Transition Diagram

```
                    ┌─────────────┐
                    │   START     │
                    │  (No OTP)   │
                    └──────┬──────┘
                           │
                           │ POST /api/otp/request
                           ▼
                    ┌─────────────┐
                    │ OTP ACTIVE  │
                    │ (60s timer) │◄───┐
                    │ Attempts: 0 │    │
                    └──────┬──────┘    │
                           │           │
            ┌──────────────┼──────────────┬─────────────┐
            │              │              │             │
            │ Correct      │ Wrong (1/3)  │ Wrong (2/3) │ 60s elapsed
            │ OTP          │ OTP          │ OTP         │
            ▼              ▼              ▼             │
     ┌──────────┐   ┌──────────┐   ┌──────────┐       │
     │VERIFIED  │   │ ACTIVE   │   │ ACTIVE   │       │
     │ (Delete  │   │Attempts:1│   │Attempts:2│       │
     │  data)   │   └────┬─────┘   └────┬─────┘       │
     └──────────┘        │              │             │
                         │              │             │
                         │ POST /resend │             │
                         └──────────────┘             │
                                                      │
                    ┌─────────────┐                   │
                    │  EXPIRED    │◄──────────────────┘
                    │ (No data)   │
                    └──────┬──────┘
                           │
                           │ POST /resend
                           ▼
                    ┌─────────────┐
                    │   ERROR     │
                    │  (404 Not   │
                    │   Found)    │
                    └─────────────┘

            Wrong (3/3) OTP
                   │
                   ▼
            ┌─────────────┐
            │   LOCKED    │
            │ (5 min)     │
            │ Delete data │
            └──────┬──────┘
                   │
                   │ 300s elapsed
                   ▼
            ┌─────────────┐
            │  UNLOCKED   │
            │ Can create  │
            │ new payment │
            └─────────────┘
```

## Summary

- **3 Main States**: No OTP → Active OTP → Verified/Expired/Locked
- **3 Redis Keys**: `otp:{id}`, `otp_attempts:{id}`, `otp_lock:{id}`
- **3 Attempts**: User can try 3 times before lock
- **60 Seconds**: OTP expiration time
- **300 Seconds**: Lock duration (5 minutes)
- **5 Endpoints**: Request, Verify, Resend, Status, Cancel
