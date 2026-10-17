# NETSCOPE - Database Report

DATABASE REPORT

**NETSCOPE**

IT Help Desk and Asset Management System



NAME: _______________________

COURSE CODE: CSC 394

MATRIC NO: _______________________

DEPARTMENT: COMPUTER SCIENCE

FACULTY: _______________________

SCHOOL: _______________________



IN PARTIAL FULFILMENT OF THE REQUIREMENTS FOR

THE AWARD OF BACHELOR OF SCIENCE (B.Sc.) IN COMPUTER SCIENCE



SUPERVISOR: _______________________

_______________________, 20______

---

## TABLE OF CONTENTS

*A generated table of contents is available in the .docx version of this document.*

---

## 1.  INTRODUCTION

This report documents the database of NETSCOPE, the IT help desk and asset management system described in the accompanying project report. The database is the part of the application that holds everything the system knows: the user accounts and the role each one holds, the equipment owned by the organisation and who it is issued to, the support tickets raised by staff and the technician each one is assigned to, the private conversation attached to each ticket, the notifications raised for administrators, and the record of maintenance carried out on each asset.

The report explains the tools used to build and manage the database, the process followed to set it up, the design of the schema and the reasoning behind it, every table and column with its type and constraints, the keys and relationships between the tables, the controlled values that hold the data valid, the referential behaviour between related records, how the schema has evolved during development, an assessment of the integrity guarantees the database does and does not provide, and finally a set of worked SQL queries showing how the application actually reads and writes its data.

The database engine is SQLite, accessed through the Flask-SQLAlchemy object-relational mapper. Everything in this report was taken from the running schema — the definitions in the model layer, the constraints as they exist in the database file, and the queries the application issues — rather than from an earlier design document.

## 2.  SYSTEM REQUIREMENTS AND TOOLS

NETSCOPE uses a serverless, file-based relational database rather than a client-server database management system. The tools required are therefore few, and none of them requires installation beyond the Python dependencies already listed in the project requirements file.

| Requirement or tool | Version | Purpose |
|---|---|---|
| Python | 3.10 or newer | Runs the application and the command-line utilities that create and inspect the database. |
| SQLite | Bundled with Python | The database engine. It stores the entire database as a single file on disk and requires no server process, no service account and no network configuration. |
| Flask-SQLAlchemy | 3.1.1 | The object-relational mapper that lets the tables and queries be expressed as Python classes and expressions instead of hand-written SQL. |
| SQLAlchemy | Installed with Flask-SQLAlchemy | The underlying mapper, which supplies the session, the unit of work, the relationship configuration and the query builder. |
| Flask-Migrate | 4.1.0 (declared, not initialised) | A migration tool that would generate and apply versioned schema changes. It is listed in the requirements file but was never wired into the application, so it is currently unused. This is discussed in sections 4.7 and 4.9. |
| SQLite command-line client | Any | Optional. Used during development to inspect tables, review the generated DDL and run ad-hoc queries against the database file. |
| pytest | 8.3.3 | Runs the automated test suite, which exercises the database through the application using an isolated in-memory database per test. |
| Any text editor with Python support | Any | To read and edit the model definitions and to write the queries. |

It should be noted that SQLite was chosen deliberately rather than by default. For an internal system serving a single organisation from a single server, its characteristics are advantages: there is no separate process to install, configure, secure and monitor; the whole database is one file, which makes backup and inspection trivial; and it is transactional and reliable. The trade-off it makes is that it serialises writes and does not enforce foreign keys unless asked to, both of which are addressed in section 4.6 and section 4.9.

## 3.  DATABASE SETUP PROCESS

The database is created and configured with the following steps. The first three are performed once when the application is installed; the remaining steps are the normal development workflow.

1. Create a Python virtual environment and install the project dependencies from the requirements file. SQLite itself requires no installation, because the engine is bundled with Python.
2. Provide the connection string and the secret key through the environment. The application reads these from a .env file in the project root. The connection string is given as DATABASE_URL, for example sqlite:///instance/netscope.db. If the variable is not set, the configuration module falls back to a default path inside the instance directory.
3. Resolve the database path. The configuration module deliberately rewrites a relative SQLite path into an absolute path anchored to the project directory, so that the database file is created in the same place regardless of which directory the application was started from. A relative path that was not normalised is one of the most common causes of an application appearing to lose its data after a restart.
4. Create the tables by running the initialisation command. This translates the six model classes into their table definitions and creates them, together with their primary keys, unique constraints, foreign keys and indexes.
5. Reconcile the schema. On every startup the application inspects the existing tables and adds any column that the model defines but the table is missing. This exists because the schema changed after the first deployment and no migration tool had been configured; section 4.7 explains the mechanism and why it should be replaced.
6. Create the first administrator account using the management command. Administrator accounts cannot be created through the public registration page, so this command bootstraps the system.
7. Verify the setup with the SQLite command-line client, confirming that the six tables, the indexes and the unique constraints exist and that the administrator row was written.

The commands used are:

```sql
# 1. dependencies
python -m pip install -r requirements.txt

# 2. configuration (create .env in the project root)
SECRET_KEY=replace-with-a-secure-secret-key
DATABASE_URL=sqlite:///instance/netscope.db

# 3. create the tables
flask --app run.py init-db

# 4. create the first administrator
flask --app run.py create-admin --username admin \
    --email admin@example.com --password StrongPassword123

# 5. inspect the result
sqlite3 instance/netscope.db ".tables"
sqlite3 instance/netscope.db ".schema tickets"
```

The initialisation command accepts a --drop flag, which destroys the existing tables before recreating them. This is intended only for a clean development reset and must never be used against a database holding data that matters.

## 4.  DATABASE DESIGN

### 4.1  Design Approach

The schema is designed in third normal form: each table represents one kind of entity, each column holds one attribute of that entity, and nothing is stored that could be derived from something else. The design followed five decisions.

- Integer surrogate keys. Every table uses an auto-incrementing integer as its primary key rather than a natural key such as a username or an asset tag. Natural keys are still present and still unique, but they are not used as the identifier. This means a person may change their username, or an asset tag may be corrected, without every related row having to be rewritten.
- One table per entity, with no duplication. The role of a user is stored once, on that user's row. A ticket stores the identifier of its creator rather than the creator's name, so a ticket cannot disagree with the user table about who the person is.
- Ownership expressed as a foreign key. Tables that belong to a user carry an ownership column referencing that user. This is what makes it possible to express access control as a database filter — a staff member's tickets are the rows whose creator is that user — rather than as a rule that has to be re-implemented in every query.
- Controlled vocabularies enforced in the application. Values such as ticket status, priority, category and support type are restricted to fixed sets. Because SQLite has no native enumerated type, these restrictions are applied in application code rather than by the database. The consequences of that choice are assessed in section 4.9.
- Historical facts are recorded, not inferred. The diagnostic steps, the actions taken, the resolution notes and the outcome are stored as they were entered, together with the time the ticket was resolved. The system deliberately does not attempt to recompute them later.

One relationship in the domain is not modelled as a key, and it is worth stating plainly here because it is the schema's most significant gap. In the real world a support ticket is usually about a particular device. The schema stores no foreign key from a ticket to an asset. The application instead guesses whether a complaint concerns equipment by searching the ticket's title and description for words such as 'device', 'computer' and 'laptop'. The consequence is that equipment fault history cannot be queried reliably, and that the guess can be wrong in both directions. Section 4.9 returns to this, and section 6 recommends the correction.

### 4.2  Entity Relationship Overview

The database has six tables. The users table sits at the centre of the schema: every other table reaches it either directly, through a foreign key, or through a chain of them. This centrality is deliberate, because nearly every access rule in the application is expressed as a question about the current user.

The relationships are as follows:

- A user has many assets — the equipment currently issued to them. This is a one-to-many relationship, optional on both sides: a user may have no equipment issued, and an asset may be held by nobody.
- A user has many tickets as the creator and many tickets as the assigned technician. These are two separate one-to-many relationships between the same pair of tables, which is why the tickets table carries two different foreign keys to users and why the relationship definitions must state explicitly which key each one uses.
- A ticket has many messages and many notifications. Each of these is a one-to-many relationship with a mandatory ticket on the child side: a message or a notification cannot exist without the ticket it belongs to.
- A user sends many ticket messages and receives many notifications. Both are one-to-many relationships from users.
- A user, acting as technician, records many maintenance logs.
- An asset has many maintenance logs. Each log records one visit to that device.

The same structure expressed as a diagram is shown below.

```sql
                        +-------------------+
                        |       users       |
                        |-------------------|
                        | id           (PK) |
                        | username  (UQ)    |
                        | email     (UQ)    |
                        | password_hash     |
                        | role              |
                        | is_approved       |
                        | is_super_admin    |
                        | created_at        |
                        +---------+---------+
          +--------------------+---+---+---------------------+
          |                        |                         |
          | 1                      | 1..*                    | 1
          |                        |                         |
          v                        v                         v
+------------------+    +--------------------+    +-------------------+
|     assets       |    |      tickets       |    |    notifications  |
|------------------|    |--------------------|    |-------------------|
| id         (PK)  |    | id           (PK)  |<-1-| ticket_id    (FK) |
| asset_tag  (UQ)  |    | title              |    | recipient_id (FK) |
| serial_no  (UQ)  |    | description        |    | message           |
| name             |    | priority           |    | link              |
| category         |    | status             |    | is_read           |
| brand/model      |    | category           |    | created_at        |
| department       |    | support_type       |    +-------------------+
| location         |    | remote_support_id  |
| status           |    | resolution_method  |
| assigned_to_id(FK)|   | diagnostic_steps   |
| purchase_date    |    | actions_taken      |
| created_at       |    | resolution_notes   |
+--------+---------+    | resolution_outcome |
         | 1            | resolved_at        |
         |              | created_by_id (FK) |
         |              | technician_id (FK) |
         |              | created_at         |
         |              | updated_at         |
         |              +---------+----------+
         | 1..*                   | 1..*
         v                        v
+------------------+    +--------------------+
| maintenance_logs |    |   ticket_messages  |
|------------------|    |--------------------|
| id         (PK)  |    | id           (PK)  |
| asset_id   (FK)  |    | ticket_id    (FK)  |
| technician_id(FK)|    | sender_id    (FK)  |
| description      |    | content            |
| cost             |    | created_at         |
| performed_at     |    +--------------------+
+------------------+
```

(PK) marks a primary key, (FK) a foreign key and (UQ) a unique key. All three foreign keys shown pointing into the tickets table — from notifications, ticket_messages and back to users — are mandatory, meaning a child row cannot be written without a valid parent.

### 4.3  Tables and Columns

Each table is described below with its columns, their types, and the keys and constraints that apply to them. The types shown are the definitions used by the mapper; SQLite itself stores them using its own type affinity rules, but the declared types are what the application and any future migration to a server-based database will rely on.

#### 4.3.1  users

Stores every account in the system, the role it holds and its account state. This is the table at the centre of the schema.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | Primary key, auto-increment | Surrogate identifier for the account. |
| username | VARCHAR(64) | Not null, unique, indexed | The name the user signs in with. Unique and indexed because login looks it up directly. |
| email | VARCHAR(120) | Not null, unique, indexed | The user's email address, also accepted as a login identifier. |
| password_hash | VARCHAR(256) | Not null | The salted one-way hash of the password. Sized at 256 characters so that a modern memory-hard hash, which is far longer than a legacy digest, fits comfortably. Stored as Werkzeug's self-describing scrypt format, so the algorithm and its parameters are recorded inside the value itself. |
| role | VARCHAR(20) | Not null, default 'staff' | One of admin, staff or technician. This value drives every authorisation decision in the application. |
| is_approved | BOOLEAN | Not null, default true | Whether the account may sign in. The login view refuses a session to an account whose flag is false. |
| is_super_admin | BOOLEAN | Not null, default false | Distinguishes the account entitled to approve other accounts and to create further administrators. |
| created_at | DATETIME | Not null | When the account was created. Set by the application at the moment of insertion. |

#### 4.3.2  assets

Stores every item of equipment owned by the organisation, its identity, its location, its condition and the member of staff it is currently issued to.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | Primary key, auto-increment | Surrogate identifier for the asset. |
| asset_tag | VARCHAR(64) | Not null, unique | The human-readable inventory label physically attached to the device. Masked at creation, because two devices carrying the same label would make the register untrustworthy. |
| name | VARCHAR(120) | Not null | A short descriptive name for the item. |
| category | VARCHAR(50) | Not null | The kind of equipment. Free text, validated only in the application, so the values in use are broad and inconsistent: laptop, printer, monitor, network, peripheral and display all appear in the development data. |
| brand | VARCHAR(80) | Nullable | The manufacturer. Added after the initial release. |
| model | VARCHAR(120) | Nullable | The model name or number. |
| serial_number | VARCHAR(120) | Not null, unique | The manufacturer's serial number. Unique, because it is the only identifier that cannot be reassigned by mistake, and because warranty and support claims depend on it. |
| department | VARCHAR(80) | Nullable | The part of the organisation that owns or uses the equipment. |
| location | VARCHAR(120) | Nullable | Where the item physically is, which for a portable device is normally the office of the person holding it. |
| status | VARCHAR(30) | Not null, default 'Available' | One of Available, Assigned, Maintenance or Retired. The application keeps this consistent with the assignment: issuing an asset sets it to Assigned, and assigning a retired asset is refused. |
| assigned_to_id | INTEGER | Nullable, foreign key to users(id) | The member of staff currently holding the asset. Null means the asset is in the pool. |
| purchase_date | DATE | Nullable | The date the item was bought. A date rather than a timestamp, because the time of purchase is not meaningful. |
| created_at | DATETIME | Not null | When the asset was registered. |

The generated table also carries a duplicate unique constraint on asset_tag and on serial_number — the same columns are declared unique both on the column and again as an explicit table-level constraint. SQLite accepts this and creates the constraint twice, so it is harmless, but it is redundant and one of the two declarations should be removed.

#### 4.3.3  tickets

Stores every support request, the whole of its work lifecycle, and the record of how it was resolved. This is the busiest table in the schema and the one that carries the most business meaning.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | Primary key, auto-increment | Surrogate identifier for the ticket. |
| title | VARCHAR(150) | Not null | A one-line summary of the fault. |
| description | TEXT | Not null | The full account given by the person reporting the problem. TEXT rather than a bounded string, because a description has no sensible length limit. |
| priority | VARCHAR(20) | Not null, default 'Medium' | One of Low, Medium, High or Urgent. Stored on the ticket rather than derived, because priority is a judgement the requester makes at the time and may legitimately differ from the category. |
| status | VARCHAR(30) | Not null, default 'Open' | One of Open, In Progress, Resolved or Closed. The transitions between these values are enforced in the application, not by the database. |
| category | VARCHAR(50) | Not null | One of Hardware, Software, Network or Access. Used by the reports to show which kinds of fault dominate. |
| support_type | VARCHAR(30) | Nullable | On-site or Remote. Nullable because the field was added after the table was first created, so tickets raised before then have no value. |
| remote_support_id | VARCHAR(120) | Nullable | The remote access identifier, such as an AnyDesk number, supplied by the requester when the support type is Remote. Capturing it at the point of reporting saves the technician from having to ask for it before starting work. |
| resolution_method | VARCHAR(30) | Nullable | How the fault was actually dealt with: Remote Support or On-site Support. This may differ from the originally requested support type, and the difference is itself useful information. |
| diagnostic_steps | TEXT | Nullable | What the technician checked and what they found. This is the column that makes the system a knowledge base rather than only a queue. |
| actions_taken | TEXT | Nullable | What was actually done to address the fault. |
| resolution_notes | TEXT | Nullable | The closing summary. The application requires this to be present and to be at least ten characters long before a ticket may be marked Resolved. |
| resolution_outcome | VARCHAR(30) | Nullable | Resolved or Unable to Resolve. If the outcome is Unable to Resolve, the application refuses to resolve the ticket and returns it to In Progress. |
| resolved_at | DATETIME | Nullable | The moment the ticket was resolved. Kept separate from updated_at so that the resolution time survives later edits to the record. |
| created_by_id | INTEGER | Not null, foreign key to users(id) | The member of staff who raised the ticket. Mandatory, because a ticket with no requester would have nobody to report back to. |
| technician_id | INTEGER | Nullable, foreign key to users(id) | The technician assigned to the work. Null means the ticket is unassigned and is the administrator's queue. |
| created_at | DATETIME | Not null | When the ticket was raised. |
| updated_at | DATETIME | Not null | When the ticket was last changed. Maintained by the mapper on every update, and used to sort the queue and ticket lists so that the most recently touched work appears first. |

#### 4.3.4  ticket_messages

Stores the private conversation attached to a ticket, in which the person who raised it and the technician assigned to it exchange clarification.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | Primary key, auto-increment | Surrogate identifier for the message. |
| ticket_id | INTEGER | Not null, foreign key to tickets(id), indexed | The ticket the message belongs to. Indexed because every conversation is read by filtering on this column. |
| sender_id | INTEGER | Not null, foreign key to users(id) | Who wrote the message. Access control is applied by the application: only the ticket's creator and its assigned technician may read or write here. |
| content | TEXT | Not null | The body of the message. |
| created_at | DATETIME | Not null | When the message was sent. Messages are ordered by this column so the conversation reads in the order it happened. |

Note the absence of a read flag. Both participants see the whole conversation, so an unread marker was not needed here. Administrators receive unread tracking instead, which is why that flag exists on the notifications table and not on this one.

#### 4.3.5  notifications

Stores the alerts raised for administrators. When a member of staff creates a ticket, one row is written for each administrator, and the row is delivered live over the existing connection and also shown in the notification panel on the next page load.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | Primary key, auto-increment | Surrogate identifier for the notification. |
| recipient_id | INTEGER | Not null, foreign key to users(id) | The administrator the alert is addressed to. One row per administrator rather than one shared row, so that each administrator can read or dismiss the alert independently. |
| ticket_id | INTEGER | Not null, foreign key to tickets(id) | The ticket that caused the alert. Mandatory, which means the table currently cannot hold a notification about anything other than a ticket. Notifying somebody that an asset was issued would require this constraint to be relaxed. |
| message | VARCHAR(255) | Not null | The text shown to the administrator, for example 'a user submitted a High Network ticket'. The sender's name is written into the text at the moment of creation rather than being resolved later, so the message reads in the past tense as it did when it was raised. |
| link | VARCHAR(255) | Not null | The destination to open when the notification is clicked. Stored at creation time rather than being computed by the interface, so the notification continues to point at the right record even if the routing changes. |
| is_read | BOOLEAN | Not null, default false | Whether the administrator has seen the alert. The unread count is this column counted for the current user. |
| created_at | DATETIME | Not null | When the alert was raised. The panel shows the eight most recent, newest first. |

The requirement that a notification always belongs to a ticket is worth noticing, because it is exactly the kind of thing that turns into an awkward migration later. A design that anticipated other kinds of notification would have made the reference optional and recorded the notification type alongside it.

#### 4.3.6  maintenance_logs

Stores the record of service carried out on an asset, kept separately from tickets because maintenance is work done on a device rather than a request raised by a person.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | Primary key, auto-increment | Surrogate identifier for the log entry. |
| asset_id | INTEGER | Not null, foreign key to assets(id) | The asset that was worked on. Mandatory, because a maintenance record with no asset would be unactionable. |
| technician_id | INTEGER | Not null, foreign key to users(id) | The technician who carried out the work. This is what makes maintenance attributable, and it is what the per-technician activity report counts. |
| description | TEXT | Not null | What was done to the asset. |
| cost | FLOAT | Not null, default 0.0 | The cost of the work. Stored as a floating-point number, which is a genuine weakness: monetary values should be held in an exact decimal type, or as an integer count of the smallest currency unit, because binary floating point cannot represent most decimal fractions exactly and accumulates drift across repeated sums. There is also no currency column, so the figure is implicitly in one currency. |
| performed_at | DATETIME | Not null | When the work was carried out. Distinct from any creation timestamp, because maintenance may be logged after the fact. |

### 4.4  Controlled Values

Several columns hold a value drawn from a fixed set rather than free text. In a server-based database these would be enumerated types or lookup tables. SQLite has no enumerated type, so in this schema the sets are enforced in the application layer, and the columns themselves are ordinary text columns with no database-level restriction.

The sets are held in one place in the application, and every route that accepts one of these values validates the submitted value against the set before storing it. The sets are:

| Column | Table | Permitted values | Enforced by |
|---|---|---|---|
| role | users | admin, staff, technician | Registration accepts only staff and technician; the account creation route additionally permits admin for a super administrator. |
| status | assets | Available, Assigned, Maintenance, Retired | The asset create and edit routes reject any other value, and the application overrides the value to keep it consistent with the assignment. |
| priority | tickets | Low, Medium, High, Urgent | The ticket creation route. |
| status | tickets | Open, In Progress, Resolved, Closed | The creation route fixes it to Open; the technician and administrator routes validate the requested value and additionally check that the transition from the current status is legal. |
| category | tickets | Hardware, Software, Network, Access | The ticket creation route. |
| support_type | tickets | On-site, Remote; or null | The ticket creation route. Remote additionally requires a remote support identifier. |
| resolution_method | tickets | Remote Support, On-site Support; or null | The technician resolution route. |
| resolution_outcome | tickets | Resolved, Unable to Resolve; or null | The technician resolution route, which additionally refuses to resolve a ticket whose outcome is Unable to Resolve. |
| category | assets | (no fixed set) | Not validated. This is the one controlled vocabulary that was never enforced, and the development data already shows the result: laptop, printer, monitor, network, peripheral and display are all in use, and none of them matches the ticket categories they sit beside. |

The consequence of enforcing these sets in code rather than in the database is examined in section 4.9. It is worth stating the principle here: the database is the last line of defence for data validity, and a schema that relies entirely on application code has no defence at all against a direct write, a migration script, or a future code path that forgets to validate.

### 4.5  Keys, Indexes and Relationships

The schema defines the following keys and indexes.

| Kind | Table and column(s) | Purpose |
|---|---|---|
| Primary key | Every table: id (INTEGER, auto-increment) | A stable, unchanging identifier for each row, independent of any value a user can edit. |
| Unique key | users.username | Prevents two accounts sharing a login name. |
| Unique key | users.email | Prevents two accounts sharing an email address, which would make email-based login ambiguous. |
| Unique key | assets.asset_tag | Prevents two devices carrying the same inventory label, which would defeat the purpose of the register. |
| Unique key | assets.serial_number | Prevents the same physical device being registered twice under different labels. |
| Foreign key | assets.assigned_to_id to users(id) | Records which member of staff holds the equipment. |
| Foreign key | tickets.created_by_id to users(id) | Records who raised the ticket. Mandatory. |
| Foreign key | tickets.technician_id to users(id) | Records who is assigned to the work. Optional, because a ticket waits unassigned. |
| Foreign key | ticket_messages.ticket_id to tickets(id) | Attaches each message to its conversation. Mandatory. |
| Foreign key | ticket_messages.sender_id to users(id) | Records who wrote the message. Mandatory. |
| Foreign key | notifications.recipient_id to users(id) | Records which administrator the alert is for. Mandatory. |
| Foreign key | notifications.ticket_id to tickets(id) | Records which ticket caused the alert. Mandatory. |
| Foreign key | maintenance_logs.asset_id to assets(id) | Attaches each maintenance entry to the asset it concerns. Mandatory. |
| Foreign key | maintenance_logs.technician_id to users(id) | Records who carried out the work. Mandatory. |
| Index | users.username, users.email | Created by the mapper because these columns are declared indexed as well as unique. They make the login lookup, which runs on every sign-in attempt, a direct lookup rather than a table scan. |
| Index | ticket_messages.ticket_id | The only hand-chosen index in the schema. Every time a ticket is opened its whole conversation is read by filtering on this column. |

The gap that stands out is the absence of indexes on the columns the application filters and counts on most heavily: tickets.status, tickets.technician_id and tickets.created_by_id, assets.status and assets.assigned_to_id, notifications.recipient_id combined with is_read, and maintenance_logs.asset_id. Every one of the dashboard figures, every role-scoped list and the technician queue is produced by filtering on one of these columns, and none of them is indexed.

At the present scale this costs nothing measurable — the tables hold tens of rows and SQLite scans them instantly. It is recorded here because it is the change that will be needed first as data accumulates, and because adding an index later is trivial while diagnosing a slow dashboard under load is not. The columns also become more expensive to leave unindexed with every cascade delete, because SQLite must scan the child table to find the rows to remove.

For completeness, the two most heavily used read patterns and the index that would address each are shown below.

```sql
-- A staff member's own tickets, ordered by recency
CREATE INDEX ix_tickets_created_by ON tickets (created_by_id, updated_at DESC);

-- A technician's queue, ordered by recency
CREATE INDEX ix_tickets_technician ON tickets (technician_id, updated_at DESC);

-- Dashboard counters and report groupings
CREATE INDEX ix_tickets_status   ON tickets (status);
CREATE INDEX ix_assets_status    ON assets  (status);
CREATE INDEX ix_assets_assigned  ON assets  (assigned_to_id);

-- The unread badge, which runs on every page render for an administrator
CREATE INDEX ix_notifications_unread ON notifications (recipient_id, is_read);
```

### 4.6  Referential Actions and Cascade Behaviour

Cascade behaviour in this schema is configured in the object-relational mapper, not in the database. Every relationship from a user to the rows that belong to that user is declared with a cascade that deletes the children when the parent is deleted, and the same applies from a ticket to its messages and notifications, and from an asset to its maintenance logs.

| Parent deleted | Rows deleted with it | Assessment |
|---|---|---|
| A user | Their assigned assets, the tickets they raised, the tickets assigned to them as technician, their maintenance logs, their notifications | The widest cascade in the schema, and the most consequential. Deleting one account removes the equipment record of what that person was issued, every fault they reported, every fault they fixed, and the entire maintenance history they contributed. For an account created in error this is correct behaviour. For the account of somebody who has left the organisation it destroys the operational history the system exists to keep. |
| A ticket | Its messages and its notifications | Correct and necessary. A conversation or an alert with no ticket behind it is meaningless and would be unreadable. |
| An asset | Its maintenance logs | Defensible but lossy. Deleting a device also deletes the record of what was spent keeping it running, so the organisation loses its maintenance cost history for equipment it has disposed of. Retiring an asset rather than deleting it avoids this, which is what the Retired status is for. |

There are two points to make about how these cascades are enforced. The first is that they are enforced in Python rather than in SQL. The table definitions do not carry an ON DELETE CASCADE clause; the behaviour is produced by the mapper when it issues the delete. A row removed by a direct SQL statement, a migration script or an external tool would therefore behave differently, leaving child rows behind rather than removing them.

The second is that SQLite does not enforce foreign keys at all unless the setting is turned on for the connection, and the application never turns it on. This means the foreign keys in this schema are, at the database level, documentation rather than enforcement: the database will happily accept a row whose parent identifier does not exist. Referential integrity in NETSCOPE currently depends entirely on application code always writing valid identifiers, which is a weaker guarantee than it appears to be from reading the table definitions.

Enabling the setting is a one-line change to how the engine is configured, and it should be done together with a decision about whether user deletion should cascade at all. The alternative to cascading is to prevent the deletion of a user who still has history, and to provide a deactivation state instead. That is the design a production support system would normally take, because staff turnover is routine while the loss of a maintenance history is not recoverable.

### 4.7  Schema Evolution

The schema changed three times after the first version was deployed, and it is worth documenting how, because the mechanism used is a design decision with real consequences.

| Change | Columns added | Reason |
|---|---|---|
| Account state | users.is_approved, users.is_super_admin | To distinguish the administrator entitled to approve accounts and create other administrators from those who may only manage day-to-day work. |
| Ticket resolution and support | tickets.support_type, tickets.remote_support_id, tickets.resolution_method, tickets.diagnostic_steps, tickets.actions_taken, tickets.resolution_notes, tickets.resolution_outcome, tickets.resolved_at | The original ticket table recorded only that work had been done. These columns were added so that the diagnostic steps, the actions taken, the resolution and the time of resolution would be preserved rather than lost when a ticket closed. |
| Asset metadata | assets.brand, assets.model, assets.department, assets.location | The register originally identified a device only by its tag and serial number, which was not enough to answer where a device was or who was responsible for it. |

Because no migration tool had been configured before the first deployment, none of these changes could be applied by a versioned migration. Instead the application performs a reconciliation pass at every startup. It inspects the existing tables, compares the columns present against the columns the models define, and issues an ALTER TABLE statement for each one that is missing. It then applies data corrections — marking existing accounts as approved, and promoting the earliest administrator to the super-administrator flag.

This approach has four weaknesses, which is why it should be replaced:

- It is not versioned and therefore not reversible. There is no record of what the schema looked like at any earlier point, and no way to undo a change.
- It only ever adds columns. It cannot rename one, change its type, move data between tables, or remove something safely, so the first change of that kind will have to be handled by hand against a live database.
- It runs on every startup in every environment, including any future production deployment, which means the application has write access to its own schema at boot. A schema change should be an explicit, reviewed act rather than a side effect of starting the process.
- The data corrections it performs are not idempotent in intent even though they are in effect. Repeatedly promoting the earliest administrator to super administrator on every startup means an operator can never demote that account.

A migration tool is already listed in the project requirements file. Initialising it and converting the three changes above into revision files would take little time, and the reconciliation routines could then be removed. This is the recommendation in section 6.

### 4.8  Normalisation

The schema is in third normal form. The reasoning is set out briefly below, because normalisation is easiest to defend when the specific dependency being removed is named.

| Normal form | Requirement | How the schema satisfies it |
|---|---|---|
| First normal form | Every column holds a single atomic value, and no column holds a repeating group. | No column stores a list or a delimited string. The one place where a repeating group naturally arises — the messages belonging to a ticket — is modelled as its own table with one row per message, rather than as several message columns on the ticket. |
| Second normal form | Every non-key column depends on the whole primary key, not part of it. | Every table uses a single-column surrogate primary key, so no non-key column can depend on only part of a composite key. The requirement is satisfied trivially by the design choice rather than by accident. |
| Third normal form | No non-key column depends on another non-key column. | This is where the meaningful decisions were made. A ticket does not store the name or the email of the person who raised it, only the identifier, so the ticket cannot disagree with the user table about who that person is. A notification does not store the title of its ticket, only the identifier. A maintenance log does not store the name of the technician, only the identifier. Every one of these is a transitive dependency that was deliberately removed. |

Two exceptions to the third normal form are present, and both are deliberate:

- assets.status can be derived from assigned_to_id: if the asset is assigned to somebody its status is Assigned. The column is kept anyway because the status carries two values that cannot be derived at all — Maintenance and Retired — and because the reports group by it directly. The cost is that the two columns must be kept consistent, which the application does explicitly on every assignment, unassignment and retirement.
- notifications.message embeds the sender's name, the ticket's priority and its category as prose, rather than storing the identifiers and composing the text when the alert is displayed. This is a denormalisation for read convenience and for historical accuracy: the alert reads as it read at the moment it was raised, which is the behaviour one wants from a notification.

Both exceptions are defensible, and both are worth naming explicitly so that a later reader knows they were chosen rather than missed.

### 4.9  Assessment of Data Integrity

This section states plainly which integrity guarantees the database provides by itself and which ones rest on the application behaving correctly. The distinction matters because the two fail in different ways: a database guarantee holds no matter who writes the data, while an application guarantee holds only as long as every writer remembers to apply it.

| Guarantee | Provided by the database? | Notes |
|---|---|---|
| Primary key uniqueness | Yes | Enforced by the engine on every insert, from any source. |
| Unique username and email | Yes | Enforced by unique indexes. |
| Unique asset tag and serial number | Yes | Enforced by unique indexes, though declared twice, as noted in section 4.3.2. |
| Not-null constraints | Yes | Enforced by the engine, which refuses a null in any column declared not null. |
| Foreign key validity | No, as the application is currently configured | SQLite does not enforce foreign keys unless the setting is enabled per connection, and the application does not enable it. A row referencing a non-existent parent would be accepted. |
| Cascade deletion | No, in the database | Produced by the mapper in Python, not by an ON DELETE clause in the schema. A direct SQL delete leaves children behind. |
| Permitted values for status, priority, category, role and outcome | No. There are no check constraints anywhere in the schema. | Enforced in the application routes. A direct write can store a value the application does not recognise, which would then be invisible in every filtered list and every report. |
| Ticket status transitions are legal | No | A workflow rule, enforced in the technician and administrator routes. It cannot be expressed as a column constraint in any case. |
| A ticket may not be resolved without resolution notes | No | Enforced in the technician route, which requires at least ten characters. |
| Money is stored exactly | No | maintenance_logs.cost is a floating-point column, so sums of cost are subject to rounding drift. |
| Timestamps preserve their time zone | No | Values are written as naive datetimes, so the offset is discarded. All stored times are effectively UTC, which is consistent as long as the system is assumed to operate in a single time zone and nothing compares a stored time to a local one. |

The pattern is clear. The database enforces everything that can be declared as a key, a uniqueness rule or a nullability rule, and it enforces nothing else. Application code is responsible for referential integrity, cascade behaviour, permitted values, workflow rules and exact monetary arithmetic.

Given that SQLite offers a straightforward way to close most of these gaps, the recommendation in section 6 is to move four of them into the database: enable foreign key enforcement on connection, add check constraints for the controlled value sets, change the maintenance cost column to an exact numeric type, and add the indexes identified in section 4.5. The workflow rules properly belong in the application either way, though they would be better placed in a service layer than inside the routes, for the reason given in the project report.

---

## 5.  SAMPLE QUERIES

The queries below are grouped by the workflow they belong to, and each one corresponds to something the application actually does. Where a query is one the application issues through the mapper, the equivalent mapper expression is noted, so the two can be compared.

Placeholders are written in angle brackets. Timestamps are shown as string literals in the format SQLite stores them in, which is YYYY-MM-DD HH:MM:SS.ffffff.

### 5.1  Accounts and Authentication

```sql
-- Register a new member of staff. The hash is produced by the application before the
-- insert; the plaintext password is never stored and never reaches the database.
INSERT INTO users (username, email, password_hash, role, is_approved, is_super_admin,
                   created_at)
VALUES ('jdoe',
        'jdoe@example.com',
        'scrypt:32768:8:1$<salt>$<derived-key>',
        'staff',
        1,
        0,
        '2026-03-09 08:15:00.000000');
```

```sql
-- Sign in: the identifier may be either the username or the email address, which is why
-- both columns are indexed. The application then verifies the hash in Python; the
-- password is never compared inside SQL.
SELECT id, username, email, password_hash, role, is_approved, is_super_admin
FROM   users
WHERE  username = 'jdoe'
   OR  email    = 'jdoe@example.com'
LIMIT  1;
```

```sql
-- Promote an existing administrator to super administrator.
UPDATE users
SET    is_super_admin = 1
WHERE  username = 'admin' AND role = 'admin';
```

```sql
-- Approve a pending account (super administrator only).
UPDATE users
SET    is_approved = 1
WHERE  id = <user_id>;
```

```sql
-- Every technician, for the assignment dropdown.
SELECT id, username
FROM   users
WHERE  role = 'technician'
ORDER  BY username;
```

### 5.2  Assets

```sql
-- Register a new asset.
INSERT INTO assets (asset_tag, name, category, brand, model, serial_number,
                    department, location, status, assigned_to_id, purchase_date,
                    created_at)
VALUES ('AST-1001', 'Dell Latitude 5420', 'Laptop', 'Dell', 'Latitude 5420',
        'SN-5541233', 'Finance', 'Head Office - Floor 2', 'Available', NULL,
        '2023-11-20', '2026-03-09 09:02:11.000000')
RETURNING id, asset_tag, status;
```

```sql
-- Issue an asset to a member of staff. The status is updated in the same statement
-- so that the two columns cannot drift apart.
UPDATE assets
SET    assigned_to_id = <staff_id>,
       status         = 'Assigned'
WHERE  id = <asset_id>
  AND  status <> 'Retired';
```

```sql
-- Return an asset to the pool.
UPDATE assets
SET    assigned_to_id = NULL,
       status         = CASE WHEN status IN ('Maintenance', 'Retired')
                             THEN status ELSE 'Available' END
WHERE  id = <asset_id>;
```

```sql
-- The staff member's own asset list. This is the whole of the access control on that
-- page: the ownership filter is the permission.
SELECT id, asset_tag, name, category, brand, model, department, location, status,
       purchase_date
FROM   assets
WHERE  assigned_to_id = <staff_id>
ORDER  BY created_at DESC;
```

```sql
-- The asset register, newest first, with the name of the person holding each item.
SELECT a.id, a.asset_tag, a.name, a.category, a.status, a.location,
       u.username AS held_by
FROM   assets a
LEFT   JOIN users u ON u.id = a.assigned_to_id
ORDER  BY a.created_at DESC;
```

```sql
-- Devices currently out for repair, and for how long.
SELECT id, asset_tag, name, department
FROM   assets
WHERE  status = 'Maintenance'
ORDER  BY asset_tag;
```

### 5.3  Tickets: Raising and Assigning

```sql
-- A member of staff raises a ticket. Status is fixed at Open and the technician is left
-- null, because assignment is an administrative decision, not the requester's.
INSERT INTO tickets (title, description, priority, status, category, support_type,
                     remote_support_id, created_by_id, technician_id,
                     created_at, updated_at)
VALUES ('Laptop will not connect to the office Wi-Fi',
        'Since Monday the laptop sees the network but will not join it. It works on the
         home network.',
        'High', 'Open', 'Network', 'Remote', '123 456 789',
        <staff_id>, NULL,
        '2026-03-10 10:20:00.000000', '2026-03-10 10:20:00.000000')
RETURNING id, title, status, technician_id;
```

```sql
-- The administrator's queue: everything raised and not yet picked up, most recently
-- touched first.
SELECT t.id, t.title, t.priority, t.category, t.status, t.created_at,
       u.username AS raised_by
FROM   tickets t
JOIN   users   u ON u.id = t.created_by_id
WHERE  t.technician_id IS NULL
  AND  t.status IN ('Open', 'In Progress')
ORDER  BY t.updated_at DESC;
```

```sql
-- Assign a ticket to a technician. The subquery is the guard: the update affects no row
-- unless the target really holds the technician role.
UPDATE tickets
SET    technician_id = (SELECT id FROM users
                       WHERE id = <tech_id> AND role = 'technician'),
       updated_at    = '2026-03-10 11:05:00.000000'
WHERE  id = <ticket_id>;
```

```sql
-- The administrator's filtered ticket list. Each filter is optional and is only applied
-- when the corresponding query parameter was supplied.
SELECT t.id, t.title, t.priority, t.status, t.category, t.updated_at,
       creator.username    AS raised_by,
       technician.username AS assigned_to
FROM   tickets t
JOIN   users   creator    ON creator.id    = t.created_by_id
LEFT   JOIN users technician ON technician.id = t.technician_id
WHERE  (:status        IS NULL OR t.status        = :status)
  AND  (:priority      IS NULL OR t.priority      = :priority)
  AND  (:category      IS NULL OR t.category      = :category)
  AND  (:technician_id IS NULL OR t.technician_id = :technician_id)
ORDER  BY t.updated_at DESC;
```

### 5.4  Tickets: Working and Resolving

```sql
-- The technician's queue. The ownership filter is the permission check.
SELECT t.id, t.title, t.priority, t.category, t.status, t.support_type,
       t.remote_support_id, t.updated_at
FROM   tickets t
WHERE  t.technician_id = <technician_id>
ORDER  BY t.updated_at DESC;
```

```sql
-- Start work: Open becomes In Progress, and only from Open.
UPDATE tickets
SET    status     = 'In Progress',
       updated_at = '2026-03-10 11:30:00.000000'
WHERE  id = <ticket_id>
  AND  status = 'Open';
```

```sql
-- Record the resolution and close the ticket. The WHERE clause encodes the whole
-- workflow rule: the ticket must be assigned to this technician, it must currently be
-- In Progress, and the resolution notes must be present and meaningful. If any of those
-- conditions fails, no row is updated and the application reports why.
UPDATE tickets
SET    resolution_method  = 'On-site Support',
       diagnostic_steps   = 'Checked the wireless adapter driver, then tested the device
                             against a second access point to rule out hardware.',
       actions_taken      = 'Reinstalled the wireless adapter driver and rejoined the
                             device to the corporate network profile.',
       resolution_notes   = 'Driver had been replaced by a generic Windows update.
                             Reinstalled the vendor driver; connection stable after
                             twenty minutes of testing.',
       resolution_outcome = 'Resolved',
       status             = 'Resolved',
       resolved_at        = '2026-03-11 09:45:00.000000',
       updated_at         = '2026-03-11 09:45:00.000000'
WHERE  id            = <ticket_id>
  AND  technician_id = <technician_id>
  AND  status        = 'In Progress'
  AND  length(trim(coalesce(:resolution_notes, ''))) >= 10;
```

```sql
-- Search the resolution history for a fault that has been seen before, so the same
-- investigation is not repeated. This is the query the resolution columns exist to make
-- possible.
SELECT id, title, category, resolution_method, resolution_notes, resolved_at
FROM   tickets
WHERE  status = 'Resolved'
  AND  (title       LIKE '%wi-fi%'  OR description      LIKE '%wi-fi%'
   OR   actions_taken LIKE '%driver%' OR resolution_notes LIKE '%driver%')
ORDER  BY resolved_at DESC;
```

```sql
-- How each category of fault is resolved in practice: remotely or on site.
SELECT category, resolution_method, COUNT(*) AS total
FROM   tickets
WHERE  status = 'Resolved'
GROUP  BY category, resolution_method
ORDER  BY category, total DESC;
```

```sql
-- Average time from a ticket being raised to it being resolved, by category, in hours.
SELECT category,
       COUNT(*) AS resolved_count,
       ROUND(AVG((julianday(resolved_at) - julianday(created_at)) * 24.0), 1)
           AS average_hours
FROM   tickets
WHERE  resolved_at IS NOT NULL
GROUP  BY category
ORDER  BY average_hours DESC;
```

### 5.5  The Ticket Conversation

```sql
-- Write a message. The application checks first that the sender is either the ticket's
-- creator or its assigned technician, and that the ticket is not already resolved.
INSERT INTO ticket_messages (ticket_id, sender_id, content, created_at)
VALUES (<ticket_id>, <user_id>,
        'The AnyDesk window is open and waiting for you.',
        '2026-03-10 11:25:00.000000')
RETURNING id, ticket_id, sender_id, content, created_at;
```

```sql
-- Read the whole conversation, oldest first, with each sender's name.
SELECT m.id, m.content, m.created_at,
       u.username AS sender_name
FROM   ticket_messages m
JOIN   users          u ON u.id = m.sender_id
WHERE  m.ticket_id = <ticket_id>
ORDER  BY m.created_at ASC;
```

```sql
-- The three most recent messages of each ticket, for the preview panel on the ticket
-- list. The subquery ranks messages within a ticket, so the list page does not have to
-- load every conversation in full.
SELECT *
FROM   (SELECT m.ticket_id, m.content, m.created_at, m.sender_id,
               ROW_NUMBER() OVER (PARTITION BY m.ticket_id
                                  ORDER BY m.created_at DESC) AS rn
        FROM   ticket_messages m
        WHERE  m.ticket_id IN (SELECT id FROM tickets
                               WHERE created_by_id = <user_id>)) ranked
WHERE  rn <= 3
ORDER  BY ticket_id, created_at;
```

### 5.6  Notifications

```sql
-- Raise an alert for every administrator when a ticket is created. If there are three
-- administrators, this writes three rows, so that each can read or dismiss it
-- independently.
INSERT INTO notifications (recipient_id, ticket_id, message, link, is_read, created_at)
SELECT u.id,
       <ticket_id>,
       'jdoe submitted a High Network ticket',
       '/admin/tickets/' || <ticket_id>,
       0,
       '2026-03-10 10:20:01.000000'
FROM   users u
WHERE  u.role = 'admin';
```

```sql
-- The unread badge and the notification panel. The badge runs on every page render for
-- an administrator, and the panel shows the eight most recent alerts of any state.
SELECT COUNT(*) AS unread_count
FROM   notifications
WHERE  recipient_id = <admin_id> AND is_read = 0;
```

```sql
SELECT id, message, link, is_read, created_at
FROM   notifications
WHERE  recipient_id = <admin_id>
ORDER  BY created_at DESC
LIMIT  8;
```

```sql
-- Mark every alert as read when the administrator opens the panel.
UPDATE notifications
SET    is_read = 1
WHERE  recipient_id = <admin_id> AND is_read = 0;
```

```sql
-- Housekeeping: remove alerts whose ticket has been closed for more than ninety days.
DELETE FROM notifications
WHERE  ticket_id IN (SELECT id FROM tickets
                     WHERE status = 'Closed'
                       AND updated_at < datetime('now', '-90 days'));
```

### 5.7  Maintenance

```sql
-- A technician logs maintenance against an asset.
INSERT INTO maintenance_logs (asset_id, technician_id, description, cost, performed_at)
VALUES (<asset_id>, <technician_id>,
        'Replaced the fuser unit and cleaned the paper path.',
        18500.00,
        '2026-03-12 14:10:00.000000')
RETURNING id, asset_id, cost, performed_at;
```

```sql
-- The maintenance history of one asset, with the technician's name on each entry.
SELECT l.id, l.description, l.cost, l.performed_at,
       u.username AS technician
FROM   maintenance_logs l
JOIN   users            u ON u.id = l.technician_id
WHERE  l.asset_id = <asset_id>
ORDER  BY l.performed_at DESC;
```

```sql
-- Total spend per asset, highest first. Note that cost is a floating-point column, so
-- this sum is subject to the rounding drift described in section 4.3.6.
SELECT a.asset_tag, a.name,
       COUNT(l.id)  AS service_count,
       SUM(l.cost)  AS total_spend
FROM   assets          a
JOIN   maintenance_logs l ON l.asset_id = a.id
GROUP  BY a.id
ORDER  BY total_spend DESC;
```

```sql
-- Which assets are costing the most to keep running, and are therefore candidates for
-- replacement rather than further repair.
SELECT a.asset_tag, a.name, a.category, a.status,
       SUM(l.cost) AS lifetime_cost
FROM   assets          a
JOIN   maintenance_logs l ON l.asset_id = a.id
GROUP  BY a.id
HAVING SUM(l.cost) > 50000
ORDER  BY lifetime_cost DESC;
```

### 5.8  Dashboard and Reporting Queries

The dashboard issues a small number of counting queries. The four counters on the administrator dashboard are shown separately below for clarity, but they are identical in shape and differ only in the filter, which is exactly the case that a single grouped query handles better.

```sql
-- The four dashboard counters, written as one grouped query instead of four round trips.
SELECT status, COUNT(*) AS total
FROM   tickets
GROUP  BY status;
```

```sql
SELECT COUNT(*) AS total_assets FROM assets;
```

```sql
SELECT COUNT(*) AS total_users FROM users;
```

```sql
-- Ticket status distribution, for the doughnut chart on the dashboard and the reports
-- page.
SELECT status, COUNT(*) AS total
FROM   tickets
GROUP  BY status
ORDER  BY CASE status WHEN 'Open'        THEN 1
                    WHEN 'In Progress' THEN 2
                    WHEN 'Resolved'    THEN 3
                    ELSE 4 END;
```

```sql
-- Asset status distribution, for the bar chart.
SELECT status, COUNT(*) AS total
FROM   assets
GROUP  BY status;
```

```sql
-- Ticket volume over the last six months, for the line chart. The application builds the
-- six month labels in Python and counts each one with this query, because SQLite has no
-- date-truncation function and a month with no tickets must still appear on the axis as
-- a zero rather than being absent from the result.
SELECT COUNT(*) AS total
FROM   tickets
WHERE  strftime('%Y-%m', created_at) = '2026-03';
```

```sql
-- The same figure for all six months in one pass, for reporting outside the application.
SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS total
FROM   tickets
WHERE  created_at >= date('now', 'start of month', '-5 months')
GROUP  BY month
ORDER  BY month;
```

```sql
-- Technician workload: how many tickets each technician is carrying, and how many of
-- those are still open or in progress.
SELECT u.username,
       COUNT(t.id) AS assigned_total,
       SUM(CASE WHEN t.status IN ('Open', 'In Progress') THEN 1 ELSE 0 END)
           AS still_open
FROM   users   u
LEFT   JOIN tickets t ON t.technician_id = u.id
WHERE  u.role = 'technician'
GROUP  BY u.id
ORDER  BY still_open DESC;
```

```sql
-- Ticket priority distribution, for the reports page.
SELECT priority, COUNT(*) AS total
FROM   tickets
GROUP  BY priority;
```

```sql
-- Ticket category distribution, for the reports page.
SELECT category, COUNT(*) AS total
FROM   tickets
GROUP  BY category;
```

```sql
-- Unassigned tickets older than two working days, with the name of the person waiting.
-- This is the query that answers the question the informal process could not: what has
-- been reported and not yet picked up?
SELECT t.id, t.title, t.priority, t.category, t.created_at,
       u.username AS raised_by,
       ROUND(julianday('now') - julianday(t.created_at), 1) AS age_days
FROM   tickets t
JOIN   users   u ON u.id = t.created_by_id
WHERE  t.technician_id IS NULL
  AND  t.status = 'Open'
  AND  julianday('now') - julianday(t.created_at) > 2
ORDER  BY age_days DESC;
```

The same figure for the number of available assets, which the asset assignment page needs when choosing what to issue:

```sql
SELECT id, asset_tag, name, category, brand, model, location
FROM   assets
WHERE  status = 'Available'
ORDER  BY category, asset_tag;
```

---

## 6.  CONCLUSION

The NETSCOPE database provides a sound and well-organised foundation for the application. The schema is normalised to third normal form, with six tables, an integer surrogate key on each, unique keys wherever a value must not repeat, and foreign keys that express both ownership and the relationships between the records. The users table anchors the design, and that is what allows the access rules of the application to be expressed as simple ownership filters rather than as logic scattered through the code.

The design decisions that shaped the schema were made deliberately: surrogate keys so that identifiers survive the editing of natural ones; ownership as a foreign key so that permission and data are the same thing; and the resolution columns on the ticket table so that the accumulated knowledge of how faults were fixed is preserved rather than lost when a ticket closes. The last of these is what turns the system from a queue into a record.

Building and documenting the database also produced an honest account of where it is currently weak, and those weaknesses are as instructive as the parts that work. Foreign keys exist in the schema but are not enforced by the engine as the application is configured, so referential integrity rests on the application rather than on the database. The controlled value sets are enforced in application code rather than by constraints, so a value the application would never produce can still be written directly. Money is held in a floating-point column and is therefore subject to rounding drift. Cascading deletes from a user remove the operational history that person contributed, which is a loss that cannot be recovered. One genuine relationship in the domain — between a ticket and the asset it concerns — was never modelled as a key, and is guessed from text instead. And the columns the dashboards filter on most heavily carry no indexes.

None of these prevents the system from working at its current scale, and each has a straightforward remedy, set out as recommendations below. What documenting them demonstrates is the principle I took from this work: a database is not merely where the application keeps its data. It is the last point at which invalid data can be refused, and every guarantee moved from application code into the schema is a guarantee that no future code path can forget.

## RECOMMENDATIONS

### Priority 1 — correctness and security

- Enable foreign key enforcement on every database connection. Until this is done, the foreign keys in the schema document the relationships but do not protect them.
- Change maintenance_logs.cost from a floating-point column to an exact numeric type, and add a currency column, so that maintenance costs can be summed without drift.
- Decide explicitly whether deleting a user should cascade. The safer design is to block the deletion of a user who has history and to provide an inactive state instead, so that staff turnover does not destroy the maintenance record.
- Remove the database file, its backup and the compiled bytecode from version control and add an ignore file, since the repository currently distributes real account data.

### Priority 2 — data integrity

- Add check constraints for the controlled value sets — user role, asset status, ticket status, priority, category, support type and resolution outcome — so that the permitted values are enforced by the database as well as by the application.
- Introduce a controlled vocabulary for asset categories, either as a check constraint or as a lookup table, since this is the only controlled set that was never enforced and its values are already inconsistent.
- Model the relationship between a ticket and the asset it concerns as a nullable foreign key, and replace the current keyword search over the title and description. Without this, equipment fault history cannot be reported accurately.
- Make notifications.ticket_id optional and add a notification type column if notifications are ever to cover anything other than a new ticket.

### Priority 3 — performance and maintainability

- Add the indexes identified in section 4.5 on the columns most used by the dashboards, the queues and the role-scoped lists.
- Replace the startup schema-reconciliation routines with versioned migrations, converting the three changes described in section 4.7 into revision files, and remove the unused migration dependency from the requirements file if it is not going to be used.
- Remove the duplicate unique constraints on assets.asset_tag and assets.serial_number, keeping only one declaration of each.
- Move the workflow rules out of the route layer and into a service layer, so that rules such as the ticket transition table can be verified directly rather than only through the web interface.
- Add pagination to the ticket, asset and user lists before the tables grow large enough for the absence of it to be felt.
- Back up the database file on a schedule and verify that a restore works, since the entire system's data currently lives in one file on one machine.

## APPENDIX A: FULL TABLE DEFINITIONS

The definitions below are the schema as it exists in the database file, produced by the mapper from the model declarations. They are reproduced here so that the schema can be recreated exactly.

```sql
CREATE TABLE users (
    id              INTEGER NOT NULL,
    username        VARCHAR(64)  NOT NULL,
    email           VARCHAR(120) NOT NULL,
    password_hash   VARCHAR(256) NOT NULL,
    role            VARCHAR(20)  NOT NULL,
    created_at      DATETIME     NOT NULL,
    is_approved     BOOLEAN      NOT NULL DEFAULT 1,
    is_super_admin  BOOLEAN      NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email    UNIQUE (email)
);

CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE UNIQUE INDEX ix_users_email    ON users (email);
```

```sql
CREATE TABLE assets (
    id              INTEGER NOT NULL,
    asset_tag       VARCHAR(64)  NOT NULL,
    name            VARCHAR(120) NOT NULL,
    category        VARCHAR(50)  NOT NULL,
    serial_number   VARCHAR(120) NOT NULL,
    status          VARCHAR(30)  NOT NULL,
    assigned_to_id  INTEGER,
    purchase_date   DATE,
    created_at      DATETIME     NOT NULL,
    brand           VARCHAR(80),
    model           VARCHAR(120),
    department      VARCHAR(80),
    location        VARCHAR(120),
    PRIMARY KEY (id),
    CONSTRAINT uq_assets_asset_tag     UNIQUE (asset_tag),
    CONSTRAINT uq_assets_serial_number UNIQUE (serial_number),
    UNIQUE (asset_tag),        -- duplicate of the named constraint above
    UNIQUE (serial_number),    -- duplicate of the named constraint above
    FOREIGN KEY (assigned_to_id) REFERENCES users (id)
);
```

```sql
CREATE TABLE tickets (
    id                  INTEGER NOT NULL,
    title               VARCHAR(150) NOT NULL,
    description         TEXT         NOT NULL,
    priority            VARCHAR(20)  NOT NULL,
    status              VARCHAR(30)  NOT NULL,
    category            VARCHAR(50)  NOT NULL,
    created_by_id       INTEGER      NOT NULL,
    technician_id       INTEGER,
    created_at          DATETIME     NOT NULL,
    updated_at          DATETIME     NOT NULL,
    support_type        VARCHAR(30),
    remote_support_id   VARCHAR(120),
    resolution_method   VARCHAR(30),
    diagnostic_steps    TEXT,
    actions_taken       TEXT,
    resolution_notes    TEXT,
    resolution_outcome  VARCHAR(30),
    resolved_at         DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY (created_by_id) REFERENCES users (id),
    FOREIGN KEY (technician_id) REFERENCES users (id)
);
```

```sql
CREATE TABLE ticket_messages (
    id          INTEGER NOT NULL,
    ticket_id   INTEGER NOT NULL,
    sender_id   INTEGER NOT NULL,
    content     TEXT    NOT NULL,
    created_at  DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (ticket_id) REFERENCES tickets (id),
    FOREIGN KEY (sender_id) REFERENCES users (id)
);

CREATE INDEX ix_ticket_messages_ticket_id ON ticket_messages (ticket_id);
```

```sql
CREATE TABLE notifications (
    id            INTEGER NOT NULL,
    recipient_id  INTEGER NOT NULL,
    ticket_id     INTEGER NOT NULL,
    message       VARCHAR(255) NOT NULL,
    link          VARCHAR(255) NOT NULL,
    is_read       BOOLEAN NOT NULL,
    created_at    DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (recipient_id) REFERENCES users (id),
    FOREIGN KEY (ticket_id)    REFERENCES tickets (id)
);
```

```sql
CREATE TABLE maintenance_logs (
    id             INTEGER NOT NULL,
    asset_id       INTEGER NOT NULL,
    technician_id  INTEGER NOT NULL,
    description    TEXT    NOT NULL,
    cost           FLOAT   NOT NULL,
    performed_at   DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (asset_id)      REFERENCES assets (id),
    FOREIGN KEY (technician_id) REFERENCES users (id)
);
```

## APPENDIX B: RELATIONSHIP SUMMARY

| Parent | Child | Cardinality | Parent side | Child side |
|---|---|---|---|---|
| users | assets | One to many | A user may be issued many assets | An asset is held by at most one user, or by nobody |
| users | tickets (created_by_id) | One to many | A user may raise many tickets | A ticket is raised by exactly one user |
| users | tickets (technician_id) | One to many | A technician may be assigned many tickets | A ticket has at most one technician, or none while unassigned |
| users | ticket_messages (sender_id) | One to many | A user may write many messages | A message is written by exactly one user |
| users | notifications (recipient_id) | One to many | A user may receive many alerts | An alert is addressed to exactly one user |
| users | maintenance_logs (technician_id) | One to many | A technician may record many maintenance entries | A maintenance entry is recorded by exactly one technician |
| tickets | ticket_messages | One to many | A ticket may carry many messages | A message belongs to exactly one ticket |
| tickets | notifications | One to many | A ticket may raise many alerts, one per administrator | An alert belongs to exactly one ticket |
| assets | maintenance_logs | One to many | An asset may have many maintenance entries | A maintenance entry belongs to exactly one asset |
