

https://www.linkedin.com/posts/jeba-rahat-782164293_a-simple-and-secure-login-module-for-library-activity-7404215275660836864-el2l?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEcJQVIBmZE3oa0kks3PiBJBHaaeUpc8JTE


1. Maintenance Module

Mandatory to develop to support Reports and Transactions modules.

Basic screen formatting is acceptable.

Admin has full access; user cannot access this module.

Contains chart links on all pages for navigation (optional in working application).

2. Navigation & Input Controls

Radio buttons: only one selection allowed.

Checkboxes: checked = Yes, unchecked = No.

Passwords must be hidden when typed on login pages.

3. Access Control

Admin: Maintenance, Reports, Transactions.

User: Reports, Transactions only.

4. Form Validations

Book Available: At least one textbox or dropdown must be filled; show error on page if none selected.

Search Results: Last column contains a selectable radio button.

4.1 Book Issue

Name of book: required

Author: auto-populated, non-editable

Issue Date: cannot be earlier than today

Return Date: defaults to 15 days ahead, editable but not beyond 15 days

Remarks: optional

Display errors if mandatory details missing.

4.2 Return Book

Name of Book: required

Author: auto-populated, non-editable

Serial No: mandatory

Issue Date: auto-populated, non-editable

Return Date: auto-populated, editable

Confirm navigates to Pay Fine page regardless of fine

Errors displayed if mandatory fields missing

4.3 Fine Pay

All fields populated except Fine Paid and Remarks

If no fine, confirm completes transaction

If fine exists, Fine Paid checkbox must be selected

Errors displayed if details missing; book cannot be returned until completed

4.4 Membership Management

Add Membership: all fields mandatory; select duration (6 months default)

Update Membership: membership number mandatory; auto-populate fields; extend or cancel membership (default 6 months extension)

4.5 Book Management

Add Book: select type (book default); all fields mandatory; show error if missing

Update Book: select type (book default); all fields mandatory; show error if missing

4.6 User Management

Select New or Existing user (new default)


Login Usernames & Passwords (Demo)
| Role                    | Username | Password    |
| ----------------------- | -------- | ----------- |
| **Admin**               | `admin`  | `adminpass` |
| **User / Normal Staff** | `user`   | `userpass`  |
