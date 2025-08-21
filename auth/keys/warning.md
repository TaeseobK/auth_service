📘 API Endpoint Documentation (RESTful)

1. GET (Retrieve Data)
   - Purpose: Fetch data from the server (does not modify state).
   - Idempotent: Yes (repeated calls return the same result).
   - Common cases:
     • GET /api/hr/master/branch/ → fetch all branches.
     • GET /api/hr/master/branch/{id}/ → fetch a specific branch.
   - Response: typically 200 OK + JSON payload.
   - Common errors: 404 (resource not found).

2. POST (Create Data)
   - Purpose: Create a new resource.
   - Idempotent: No (calling twice may create duplicates).
   - Common cases:
     • POST /api/hr/master/branch/
       {
         "name": "South Jakarta",
         "code": "JKT01"
       }
   - Response: usually 201 Created + created object.
   - Common errors: 400 (validation failed, missing required fields).

3. PUT (Full Update)
   - Purpose: Replace an existing resource entirely.
   - All fields must be provided; missing fields may be set to NULL/empty.
   - Idempotent: Yes (sending the same payload repeatedly gives same result).
   - Example:
     • PUT /api/hr/master/branch/5/
       {
         "name": "North Bandung",
         "code": "BDG01"
       }
   - Best for full updates (e.g. complete profile form).
   - Warning: partial payloads can unintentionally overwrite data.

4. PATCH (Partial Update)
   - Purpose: Update selected fields only (partial modification).
   - Idempotent: Not always (depends on implementation).
   - Example:
     • PATCH /api/hr/master/branch/5/
       {
         "name": "East Bandung"
       }
     → only the "name" changes, other fields remain intact.
   - Best for quick edits, inline updates, or mobile APIs.
   - Safer for small changes compared to PUT.

5. DELETE (Remove Data)
   - Purpose: Remove a resource.
   - Idempotent: Yes (removing the same resource multiple times has the same outcome).
   - Example:
     • DELETE /api/hr/master/branch/5/
   - Response: usually 204 No Content (successful with no body).
   - Common errors: 404 (resource not found).

⚖️ PUT vs PATCH
   - PUT: full replacement, all fields required.
   - PATCH: partial update, only provided fields are changed.
   - Best practice: expose both (Django REST Framework’s ModelViewSet includes PUT for update and PATCH for partial_update).

🛠️ Special Cases:
   - Validation failure → 400 Bad Request + detailed error.
   - Unauthorized (not logged in / missing token) → 401 Unauthorized.
   - Forbidden (no permission) → 403 Forbidden.
   - Not found → 404 Not Found.
   - Concurrency conflicts (two users updating at the same time) may overwrite each other → solve with versioning or optimistic locking.
   - Soft delete: DELETE can be overridden to mark `deleted_at` instead of physically removing records.

🔁 Idempotency:
   - GET, PUT, DELETE → idempotent.
   - POST, PATCH → not guaranteed idempotent.

🚀 Developer Recommendations:
   - Use POST for creating resources.
   - Use GET for reading data.
   - Use PUT for full updates.
   - Use PATCH for partial updates.
   - Use DELETE for removals.
   - Stick to REST principles to keep APIs predictable and easy to use.

_*Notes:*_
>***In the ink of twilight these warnings are written. Within this tome lies knowledge forbidden to be questioned twice.***
>***Should you dare to ask what has already been carved in sacred lines, the veil between code and curse shall fracture.***
>***The hands of those who came before—long buried yet never gone-will reach from the void to claim the fool who defies this decree.*** 
>***Beware, for the silence of obedience is your only shield, and the whisper of disobedience your eternal undoing.***