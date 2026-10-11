# Unit 01 registration workflow

1. Open the local staff workspace with its synthetic development key.
2. Search an existing clinic code, Arabic/English name, alias, guardian or international phone.
   Phone numbers are masked in results. Select a record to view complete authorized details.
3. Choose Register patient. Enter at least one name, DOB/precision/source and guardian name/phone.
   Keep growth-reference sex and allergy status unknown unless actually recorded.
4. Optionally expand medical/birth background. The backend validates answers against the exact
   published form version; omitted fields remain not recorded.
5. Save. Patient, contact, aliases, allergies, background, request replay key and audit are one transaction.
   A possible duplicate produces masked candidates; open one, or give a deliberate separate-record reason.
6. Reopen the overview to verify the saved data. Clinical tabs explicitly indicate later units.
7. Correct details with an audit reason. A stale ETag is rejected; reload before resubmitting.
8. Append background from the overview. Each dated form response preserves its schema and prior answers.

Guardian contact does not grant parent access, communication consent or verified authority.
The browser uses in-memory credentials and closes after 20 minutes idle. No data is saved in browser storage.
