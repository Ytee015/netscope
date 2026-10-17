# NETSCOPE - SIWES Project Report

SIWES REPORT

**(STUDENTS INDUSTRIAL WORK EXPERIENCE SCHEME)**



An IT Help Desk and Asset Management System



NAME: _______________________

SIWES COMPANY NAME: _______________________

MATRIC NO: _______________________

DEPARTMENT: COMPUTER SCIENCE

FACULTY: _______________________

SCHOOL: _______________________



IN PARTIAL FULFILMENT OF THE REQUIREMENTS FOR

THE AWARD OF BACHELOR OF SCIENCE (B.Sc.) IN COMPUTER SCIENCE



SUPERVISOR: _______________________

_______________________, 20______

---

## DEDICATION

I dedicate this report to Almighty God, the source of all wisdom and strength, for His guidance and protection throughout the period of my industrial training. I also dedicate it to my parents and my family, whose love, prayers and support carried me through this period, and to everyone who encouraged me to keep learning and keep building.

---

## ACKNOWLEDGEMENTS

My deepest gratitude goes to Almighty God for His grace and protection during the entire period of my training.

I sincerely appreciate my industry-based supervisor and the SIWES coordinator at _______________________, for the guidance, trust and feedback I received, and for the opportunity to work on real software during my attachment. Their mentorship shaped how I approach engineering problems.

I am grateful to the entire team at _______________________ for the collaborative working environment that made my placement a genuinely useful experience. Working alongside them showed me how real software is planned, written, reviewed and maintained.

I also thank my Head of Department, _______________________, my institution-based supervisor, _______________________, and all the lecturers of the Department of Computer Science, for their commitment to our academic and professional development.

Finally, I thank my family and friends for their unwavering support and motivation throughout this journey.

---

## TABLE OF CONTENTS

*A generated table of contents is available in the .docx version of this document.*

---

## ABSTRACT

The Students Industrial Work Experience Scheme (SIWES) is a supervised training programme established by the Industrial Training Fund (ITF) in 1973 to bridge the gap between classroom theory and professional practice. This report documents the software I designed and built during my industrial training attachment: NETSCOPE, an IT help desk and asset management system.

Organisations that provide internal information technology (IT) support usually manage requests informally, through telephone calls, walk-ins, chat messages and spreadsheets. These channels leave no reliable record of what was reported, who is working on it, what was done to fix it, or which equipment the organisation owns. NETSCOPE addresses this problem by providing a single web application in which three kinds of users work together: staff members who report faults and see the equipment assigned to them, technicians who carry out the work and record what they did, and administrators who own the inventory, manage accounts, assign work and monitor performance.

The system was built with the Python programming language and the Flask web framework, using Flask-SQLAlchemy for database access, Flask-Login for session-based authentication, Flask-SocketIO for live notifications and ticket chat, and SQLite as the database engine. It is structured as a modular monolith using Flask blueprints, with a separate blueprint for each user role and a shared model layer. Access to every page is controlled by a role-checking decorator, and the core workflows are verified by an automated test suite of sixteen tests.

This report describes the organisation, the problem the software solves, the activities I carried out, the architecture and technology stack of the system, the database design, the security model, the testing carried out, the challenges I encountered, the limitations I identified in the implementation, and my observations and contributions. The training strengthened my practical ability to design, build, test and document a complete software system.

---

## CHAPTER ONE: INTRODUCTION

### 1.1  About SIWES

The Students Industrial Work Experience Scheme (SIWES) is a planned and supervised training programme established by the Industrial Training Fund (ITF) in 1973. It was introduced to give students of tertiary institutions in Nigeria the opportunity to gain practical, hands-on experience in their fields of study before graduation, and to expose them to the equipment, tools, methods and professional practices used in industry, many of which are not available within the four walls of a classroom.

The scheme is funded by the Federal Government of Nigeria and coordinated by the ITF together with the National Universities Commission (NUC), the National Board for Technical Education (NBTE) and the National Commission for Colleges of Education (NCCE). It is accepted as part of the approved minimum academic standards for several degree programmes in Nigerian universities, and participation is a requirement for the award of the degree in Computer Science at my institution.

SIWES connects what a student learns in the classroom with the real demands of the workplace. It allows a student to apply theory to practice, to work with current tools and methods, and to understand how organisations plan, build and deliver their work. For a Computer Science student, it is the opportunity to move from writing small programs in isolation to building and shipping software that other people actually use.

### 1.2  Objectives of SIWES

The main objectives of the scheme are:

- To provide students with the opportunity to apply the theoretical knowledge gained in school to real work situations, thereby bridging the gap between theory and practice.
- To expose students to the tools, equipment, methods and work practices used in industry.
- To help students develop practical skills, good work habits and professional attitudes in their chosen fields.
- To give students the opportunity to test their interest and aptitude for a particular career before making a permanent commitment.
- To make the transition from the university to the world of work easier and to prepare students for employment after graduation.
- To strengthen the involvement of employers in the training and preparation of graduates for industry.
- To develop in students a sense of responsibility, discipline and the ability to work with others.

### 1.3  Roles of Students During SIWES

During the training period, a student is expected to:

- Comply with the rules, regulations and code of conduct of the establishment.
- Record all training activities and assignments clearly and honestly in the log book, with diagrams and sketches where applicable.
- Observe and familiarise themselves with the work environment, the processes and the tools used in the organisation.
- Participate actively in assigned tasks, meet agreed deadlines and produce work of good quality.
- Seek knowledge and guidance from supervisors and colleagues, and ask questions whenever something is not understood.
- Maintain punctuality, professional conduct and a cordial working relationship with members of staff.
- Observe confidentiality and handle the organisation's systems, data and equipment responsibly.

---

## CHAPTER TWO: ABOUT THE ORGANISATION

### 2.1  About the Organisation

_______________________ is the establishment where I carried out my six months of industrial training. It operates an information technology function that provides internal technical support to its staff and maintains the computing equipment the organisation depends on to do its work.

I was attached to the IT support function of the organisation, where the work combined day-to-day user support with software development. The internal support team is responsible for responding to faults reported by staff — problems with laptops, printers, network connectivity and user accounts — as well as keeping an accurate record of the equipment the organisation owns, who it is issued to, and its condition.

It was inside this function that the need for the software documented in this report became clear. The team was handling a growing volume of requests through informal channels, and there was no single place where the history of that work could be seen.

### 2.2  Vision and Mission

The organisation's vision is to use technology to make its operations faster, more reliable and easier to account for. Its mission, as it applies to the IT function, is to ensure that every member of staff is able to work without avoidable technical interruption, and that every piece of equipment owned by the organisation is known, tracked and properly maintained.

In practice this means the IT function is judged on two things: how quickly staff problems are resolved, and how well the organisation's equipment and support history are documented.

### 2.3  Services and Areas of Focus

The areas of focus of the IT function during my attachment were:

- End-user support — receiving, triaging and resolving faults reported by members of staff.
- Hardware and peripheral management — procurement records, issuing equipment to staff, and tracking its condition and location.
- Network and connectivity support — diagnosing problems with internet access, local network access and shared devices.
- Account and access management — creating accounts, resetting credentials and controlling who can reach which systems.
- Preventive maintenance — scheduled servicing and repair of equipment, together with a record of the cost of that work.
- Internal software development — building the tools the organisation uses to run its own support operations, of which NETSCOPE is one.

### 2.4  Office Location and Contact

Office address: _______________________

Contact: _______________________

### 2.5  The IT Support Environment

Before the software described in this report was built, IT support in the organisation followed a pattern that is very common in small and medium organisations. A member of staff with a problem would call the IT desk, walk over to it, or send a message. The person on the desk would note the problem, usually on paper or in a chat message, and then either deal with it or pass it to a colleague.

This worked, but it had four weaknesses that became more serious as the volume of requests grew:

1. There was no reliable record of what had been reported. Requests mentioned verbally or in a chat thread could be forgotten entirely, and nobody could say with confidence how many outstanding requests existed at any moment.
2. Responsibility was unclear. Because there was no formal assignment step, two people could work on the same fault, or nobody could work on it at all, without anyone noticing.
3. The work done was not documented. When a fault was fixed, the diagnostic steps taken, the action that resolved it, and the outcome were rarely written down, so the same fault would be investigated from the beginning the next time it occurred.
4. Equipment records were incomplete. The organisation did not have a single accurate list of its devices, which of them were issued to which member of staff, or what maintenance had been carried out on them and at what cost.

These weaknesses are precisely the problem that NETSCOPE was built to solve, and they define the requirements that shaped its design.

---

## CHAPTER THREE: ACTIVITIES, THE SOFTWARE BUILT, TOOLS AND SKILLS

### 3.1  Overview of Activities

Throughout my attachment I worked as a software engineering intern within the IT support function. My activities covered the full software development process rather than a single stage of it:

- Requirements gathering — sitting with the support team to understand how requests actually arrive and where the existing process broke down.
- System design — deciding the user roles, the workflows each role follows, the data that must be stored, and how the application would be structured in code.
- Database design — modelling the entities, their columns, their relationships and the constraints that keep the data valid.
- Implementation — writing the backend routes, the authorisation rules, the database models, the Jinja2 templates and the client-side JavaScript.
- Real-time features — implementing live admin notifications and the private ticket communication channel.
- Testing — writing and running an automated test suite covering authentication, permissions, asset management and the ticket lifecycle.
- Documentation — writing the project README, the project documentation and the database report that accompanies this one.

My main and most significant piece of work was the design and implementation of NETSCOPE, described in detail below.

### 3.2  The Software Built: NETSCOPE

NETSCOPE is an IT help desk and asset management system. It is a web application in which three kinds of users — administrators, staff and technicians — work from the same set of records to report, assign, resolve and account for IT support work.

#### 3.2.1  The Problem

The problem NETSCOPE solves is the absence of a single, reliable record of IT support work and of the equipment that work is carried out on. When support requests are handled through phone calls, walk-ins and chat messages, the organisation ends up with three specific failures:

- No visibility. Administrators cannot see how many requests are open, how long they have been open, which categories of fault are most common, or which technician is carrying the most work.
- No accountability. Without a formal assignment step and a status that changes as work progresses, nobody can tell whether a reported fault has been picked up, is being worked on, or has been quietly forgotten.
- No knowledge retention. If the diagnostic steps, the actions taken and the resolution are not recorded, the organisation learns nothing from a fault it has already fixed. The same problem is diagnosed from scratch every time.

Alongside this, the equipment side of the problem is that the organisation does not know what it owns. Without a tracked asset register there is no answer to basic questions: how many laptops are available, which one is with which member of staff, which devices are due for maintenance, and what has been spent keeping them running.

#### 3.2.2  The Solution

NETSCOPE solves this by making the record the centre of the process. Instead of a fault being described in a message that disappears, it is entered into the system as a ticket, which then carries its own history from the moment it is raised to the moment it is closed.

The solution has five parts that fit together:

1. Structured reporting. A member of staff raises a ticket with a title, a description, a category (Hardware, Software, Network or Access), a priority (Low, Medium, High or Urgent) and a support type (on-site or remote). If the support is remote, the system requires the remote access identifier, so the technician does not have to ask for it later.
2. Formal assignment. Every ticket is visible to the administrators, who receive a live notification the moment it is created and assign it to a named technician. From that point the ticket is that technician's responsibility and appears in their queue.
3. A controlled work lifecycle. A ticket moves through the states Open, In Progress, Resolved and Closed. The transitions are enforced on the server, so a ticket cannot be marked Resolved without diagnostic steps and meaningful resolution notes being recorded first.
4. A recorded resolution. Before a ticket can be closed, the technician records the method used (remote or on-site support), the diagnostic steps taken, the actions taken, the resolution notes and the outcome. That record is what stops the organisation from re-solving the same problem twice.
5. A tracked asset register. Every device is registered with an asset tag, a serial number, a category, a brand, a model, a department, a location, a purchase date and a status. Assets are issued to named members of staff, and the staff members themselves can see the equipment currently assigned to them.

Two supporting features hold the process together. The first is a private conversation thread attached to each ticket, in which only the person who raised it and the technician assigned to it can exchange messages, so clarification does not have to leave the system. The second is the maintenance log, where a technician records service carried out on any asset, together with its cost, building a maintenance history per device.

#### 3.2.3  User Roles and Permissions

The application defines three roles. Every page in the system is protected by a single role-checking decorator that both requires the user to be logged in and verifies that the user's role is permitted for that page. A user who is authenticated but has the wrong role receives a 403 Forbidden page rather than the requested content.

| Role | Responsibilities in the system | Cannot do |
|---|---|---|
| Administrator | Manage user accounts; create, edit, delete and assign assets; view all tickets; assign tickets to technicians; override ticket status; view the dashboard, reports and live notifications. | Raise tickets on behalf of staff (there is no impersonation feature). |
| Staff | View the assets assigned to them; raise tickets; track the status of their own tickets; exchange messages with the assigned technician. | See other staff members' tickets or assets; assign work; edit assets; access administration pages. |
| Technician | View their own assigned queue; start work on a ticket; record diagnostic steps, actions taken and resolution notes; move a ticket to In Progress or Resolved; log maintenance against any asset. | Assign tickets to themselves or others; close tickets; manage users or assets. |

Administrator accounts are deliberately excluded from public registration. Staff and technician accounts can be created through the registration page, while administrator accounts are created either from the command line through a management command or from the user management page by an administrator who holds the super-administrator flag. This prevents a visitor from granting themselves administrative access to the system.

#### 3.2.4  Core Features

The implemented features of the system are:

- Session-based authentication using a username or an email address, with passwords stored only as salted one-way hashes.
- Role-based access control applied consistently across every route in the application.
- Ticket creation with category, priority and support-type validation, including a conditional requirement for a remote access identifier.
- Standard, auditable ticket statuses — Open, In Progress, Resolved and Closed — with server-side enforcement of the allowed transitions.
- A structured resolution record capturing the support method, diagnostic steps, actions taken, resolution notes and outcome.
- A private per-ticket conversation between the requester and the assigned technician, delivered live, and closed automatically once a ticket is resolved.
- Live administrator notifications raised the instant a ticket is created, with an unread counter and a mark-all-read action.
- Full asset lifecycle management: registration, editing, deletion, assignment to a member of staff and unassignment.
- A per-asset maintenance log recording the description, cost and date of service work.
- Administrative dashboards and a reports page presenting ticket volume, ticket status distribution, asset status distribution, ticket priorities and categories, technician workload and the maintenance history, all rendered as charts.
- A technician queue with a badge showing the number of assigned tickets that relate to equipment.
- Friendly error pages for the 403, 404 and 500 responses instead of raw framework errors.

### 3.3  System Architecture

This section describes how the application is put together. It covers the architectural style chosen, how responsibility is divided between layers, the components that make up the system, what happens when a user makes a request, how the real-time features work, and the physical structure of the project on disk.

#### 3.3.1  Architectural Style

NETSCOPE is a modular monolith. The entire application is a single deployable unit with a single runtime process and a single database file, but internally it is divided into modules that are grouped by user role: one blueprint for authentication, one for administrator functions, one for staff functions and one for technician functions.

The application is created through a factory function rather than at module import time. The factory accepts an optional configuration override, which is what allows the test suite to construct a fully isolated instance of the application backed by an in-memory database without touching the development database.

Two alternatives were considered and rejected:

- A microservice split — one service for tickets, one for assets and one for accounts. This would have introduced network calls, separate deployments, distributed transactions and operational overhead for an application that serves a single organisation from a single server. The cost was not justified by the scale.
- A single flat application module with all routes in one file. This is the simplest possible Flask structure and would have been quicker to start, but with four distinct role areas and roughly thirty routes it would have become a single file that every change had to be made in, and routing rules for one role could be broken by an edit intended for another.

The blueprint structure was chosen because it keeps the concerns of the three roles apart while preserving a single deployment unit and a single database, which is the right trade-off at this scale.

#### 3.3.2  Layered Structure

Within the monolith the code is divided into horizontal layers, each with a single responsibility. A layer only communicates with the layer directly beneath it.

| Layer | Components | Responsibility |
|---|---|---|
| Presentation | Jinja2 templates (28 files), the custom stylesheet, the client-side JavaScript module | Render the correct interface for the user's role; draw charts; open the socket connection and render live messages as they arrive. |
| Transport | Flask blueprints (auth, admin, staff, technician), Socket.IO event handlers, the JSON ticket-messages endpoint | Map URLs and socket events onto application behaviour; read and validate request input; perform permission checks; choose the response. |
| Application | The view functions themselves, together with the shared role decorator | Apply the business rules: who may do what, which ticket transitions are legal, what must be recorded before a ticket can be resolved. |
| Persistence | Six SQLAlchemy models, the shared session, the relationship and cascade configuration | Translate Python objects into rows and back; declare the schema, its keys and its relationships. |
| Storage | SQLite database file | Durable storage of all application data. |
| Cross-cutting | The role decorator, the login manager, the CSRF protector, the context processors, the error handlers | Concerns that apply to every request: authentication state, authorisation, request tokens, notifications injected into every page, and error rendering. |

It should be stated plainly that the application layer is implemented as a transaction script: the business logic lives inside the view functions rather than in a separate service or domain layer. This was a deliberate trade-off in favour of speed of development. Its consequence is that rules such as the ticket status-transition table cannot be exercised by a unit test directly; they can only be tested through the web interface. That limitation is discussed further in sections 5.3 and 6.

#### 3.3.3  Component Breakdown

The table below lists the principal components of the system and what each one does.

| Component | Location | Purpose |
|---|---|---|
| Application factory | app/__init__.py | Creates and configures the application; initialises the extensions; registers the blueprints, the socket event handlers, the context processors, the error handlers and the command-line commands. |
| Configuration | config.py | Resolves the database URL, reads environment variables, and supplies development, testing and production configurations. |
| Extensions | app/extensions.py | Holds the single shared instances of the database, login manager, CSRF protector and socket server, created without an application so that they can be bound inside the factory. |
| Models | app/models.py | Declares the six tables, their columns, their constraints, their relationships and their password helpers. |
| Authorisation decorator | app/decorators.py | Wraps a view so that it requires an authenticated session and a permitted role, raising 403 otherwise. |
| Authentication blueprint | app/blueprints/auth/ | Login, registration, logout and profile views. |
| Administrator blueprint | app/blueprints/admin/ | Dashboard, asset management, user management, ticket assignment and reporting views. |
| Staff blueprint | app/blueprints/staff/ | Staff dashboard, assigned-asset list, ticket creation and ticket detail views. |
| Technician blueprint | app/blueprints/technician/ | Technician dashboard, assigned queue, ticket resolution and maintenance logging views. |
| Templates | app/templates/ | A shared base layout plus one directory of templates per role, with error pages and a public landing page. |
| Static assets | app/static/ | The custom dark-theme stylesheet, the client-side JavaScript module and the vector logo. |
| Test suite | tests/ | Sixteen automated tests across three files covering authentication, assets and tickets. |
| Entry point | run.py | Builds the application and starts the socket-capable web server. |

#### 3.3.4  Request Lifecycle

The sequence below traces what happens when a technician records the resolution of a ticket, which exercises every layer of the architecture.

1. The browser sends a POST request to the technician ticket status URL with the resolution form fields and the request token.
2. The request first reaches the cross-cutting layer, where the session is restored from the signed cookie and the request token is checked.
3. The role decorator runs before the view. It confirms the user is authenticated and that the user's role is technician; otherwise the request is aborted with 403.
4. The view loads the ticket by its identifier, or returns 404 if it does not exist, and then verifies that this ticket is actually assigned to the current technician. Ownership is checked separately from role, because a role check alone would let any technician modify any ticket.
5. The submitted values are validated: the resolution method, the outcome and the requested status must each fall within their permitted sets.
6. The state-transition rules are applied. The transition table allows Open to In Progress and In Progress to Resolved; anything else is rejected. If the outcome is 'Unable to Resolve', the ticket is forced back to In Progress instead of being resolved. If the requested status is Resolved but the resolution notes are shorter than ten characters, the change is refused and the user is told why.
7. The model is updated — status, resolution fields, the last-updated timestamp and the resolution timestamp — and the unit of work is committed to the database as a single transaction.
8. A flash message is queued, the request is redirected to the ticket detail page, and the template renders the updated state.

#### 3.3.5  Real-Time Communication

Two features need to reach the user without a page reload: the administrator notification bell must light up when a ticket is created, and the ticket conversation must deliver messages to both participants as they are sent. Both are implemented with Socket.IO on top of the same web process.

The real-time design deliberately uses rooms, which are named groups of connections, so that a message is only sent to the sockets that are entitled to receive it:

| Room | Who joins | Events delivered |
|---|---|---|
| admin_<user id> | An administrator, after the server confirms the id belongs to the authenticated administrator and that the role is administrator. | new_ticket_notification |
| ticket_<ticket id> | Only the member of staff who raised the ticket and the technician assigned to it; the server re-checks ownership before admitting the socket to the room. | ticket_message_received |

The important architectural point is that Socket.IO events are not covered by Flask's route decorators, so a socket handler that assumed the user was authorised would be a serious vulnerability. Both the join handler for the ticket room and the message-sending handler therefore repeat the ownership check, and message sending is additionally refused once a ticket has been resolved or closed. The same rules are applied a second time in the HTTP JSON endpoint that the interface uses to send a message, so that neither entry point can be used to bypass the other.

#### 3.3.6  Project Structure

The layout of the project on disk is shown below.

```sql
netscope/
|-- run.py                     # entry point: builds the app, starts the server
|-- config.py                  # environment-aware configuration
|-- requirements.txt           # pinned Python dependencies
|-- README.md                  # setup and usage instructions
|-- app/
|   |-- __init__.py            # application factory, socket handlers, CLI commands
|   |-- extensions.py          # shared db, login manager, csrf, socket instances
|   |-- models.py              # the six SQLAlchemy models
|   |-- decorators.py          # role_required authorisation decorator
|   |-- blueprints/
|   |   |-- auth/routes.py     # login, register, logout, profile
|   |   |-- admin/routes.py    # dashboard, assets, users, tickets, reports
|   |   |-- staff/routes.py    # dashboard, assets, tickets
|   |   |-- technician/routes.py  # dashboard, queue, resolution, maintenance
|   |-- templates/             # base layout + one folder per role
|   |-- static/
|       |-- css/style.css      # custom dark glass theme
|       |-- js/main.js         # charts, notifications, live chat
|       |-- images/logo.svg
|-- instance/
|   |-- netscope.db            # SQLite database file
|-- tests/
|   |-- test_auth.py           # 5 authentication and permission tests
|   |-- test_assets.py         # 5 asset management tests
|   |-- test_tickets.py        # 6 ticket lifecycle tests
|-- documentation/             # project and database reports

```

### 3.4  Technology Stack

The application is built on Python and the Flask ecosystem. The table below lists every technology used, the version pinned in the requirements file, its role in the system, and the reason it was chosen.

| Technology | Version | Role in the system | Why it was chosen |
|---|---|---|---|
| Python | 3.10 or newer | The programming language of the whole application | Readable, widely taught, and the natural language of the Flask ecosystem. |
| Flask | 3.1.0 | Web framework: routing, request handling, templating integration | Minimal and explicit. It imposes no project structure, which allowed the role-based blueprint layout to be designed deliberately rather than inherited. |
| Flask-SQLAlchemy | 3.1.1 | ORM mapping models to SQLite tables | Removes hand-written SQL for routine operations while still allowing raw SQL where the dashboard aggregations need it. |
| Flask-Login | 0.6.3 | Session management and the current-user object | The established Flask solution for session login; supplies the user loader, the login guard and strong session protection. |
| Flask-WTF | 1.2.2 | CSRF protection and form security primitives | Provides request-token generation and validation as a single extension rather than a hand-rolled implementation. |
| Flask-SocketIO | 5.4.1 | Live notifications and ticket chat over WebSockets | Adds event-driven communication to the existing Flask process, so no separate real-time service was needed. |
| SQLAlchemy | (via Flask-SQLAlchemy) | Query building, relationships, transactions | Expresses the relationships and cascades declaratively and gives the dashboard aggregations a portable query interface. |
| SQLite | Included with Python | The database engine | Serverless, file-based and requires no installation or administration. Appropriate for an internal system on a single server, and it keeps the deployment story simple. |
| Jinja2 | (via Flask) | Server-side HTML templating | Ships with Flask; template inheritance gives every page the shared layout, navigation, notification bell and flash messages with no duplication. |
| Werkzeug | (via Flask) | Password hashing and request utilities | Its password hashing helpers produce salted, self-describing hashes, so the algorithm used is recorded inside the stored value. |
| Bootstrap | 5.3.2 (CDN) | Responsive grid, components and utility classes | A consistent, responsive interface across the dashboards without writing a component library. |
| Bootstrap Icons | 1.11.3 (CDN) | Iconography in navigation, cards and badges | Matches Bootstrap visually and needs no build step. |
| Chart.js | (CDN) | Doughnut, bar and line charts on the dashboards and reports | Charts are configured by passing a JSON specification straight from a template data attribute, so no charting code had to be written. |
| Socket.IO client | 4.7.5 (CDN) | Browser side of the live notification and chat channel | The client counterpart to Flask-SocketIO, with automatic reconnection. |
| python-dotenv | 1.0.1 | Loading environment variables from a .env file | Keeps the secret key and database URL out of the source code and out of version control. |
| email-validator | 2.2.0 | Email address validation on registration | A dependency of Flask-WTF's email field; ensures account emails have a valid form. |
| pytest | 8.3.3 | Running the automated test suite | Concise test syntax with fixtures, which suited the per-test isolated application instance used by the suite. |

### 3.5  Database Design Overview

The persistence layer is a normalised relational schema of six tables. It is documented fully in the accompanying database report, and is summarised here so that the architecture can be read as a whole.

| Table | Represents | Key relationships |
|---|---|---|
| users | Every account in the system and the role it holds | Referenced by assets, tickets, ticket messages, notifications and maintenance logs. |
| assets | Every item of equipment the organisation owns | May be assigned to one user; has many maintenance logs. |
| tickets | Every support request raised by a member of staff | Belongs to one creator; may be assigned to one technician; has many messages and notifications. |
| ticket_messages | The private conversation on a ticket | Belongs to one ticket; has one sender. |
| notifications | An alert raised for an administrator when a ticket is created | Belongs to one recipient and one ticket. |
| maintenance_logs | Service carried out on an asset | Belongs to one asset and one technician. |

The user table is the centre of the schema. Every other table reaches it either directly or through a chain of foreign keys, which is what makes role-based scoping — a staff member seeing only their own tickets and assets — expressible as a single filter on an ownership column. The relational design, the keys and the constraints are examined in detail in the accompanying database report.

### 3.6  Security Model

Security in the application rests on five controls.

- Authentication. Login accepts either a username or an email address. On success the previous session is cleared before the new one is issued, which prevents session fixation. The login manager is configured with strong session protection, so a session that appears to be used from a different client is invalidated.
- Password storage. Passwords are never stored or logged in readable form. Only a salted one-way hash is persisted. The hashes stored in the development database are in Werkzeug's scrypt format, and because the algorithm parameters are recorded inside each stored value, the hashing method can be strengthened later without invalidating existing accounts.
- Authorisation. Every route is wrapped by a single role-checking decorator. Authorisation is enforced entirely on the server; hiding a navigation link in a template is a convenience for the user, never the security control itself.
- Ownership checks. Role is necessary but not sufficient. Views that operate on a specific record verify that the record belongs to the current user — that a staff member's ticket is theirs, or that a technician's ticket is assigned to them. This is what stops one technician from editing another technician's work.
- Input validation. Categories, priorities, statuses, support types and outcomes are all checked against their permitted sets on the server before being stored, and asset creation additionally verifies that an assignment refers to a user who really holds the staff role.

Alongside these controls there are configuration weaknesses which are identified honestly in section 5.3 and carried into the recommendations in section 6, because a security model is only credible if its gaps are named.

### 3.7  Testing and Validation

A suite of sixteen automated tests was written using pytest and is included in the project under the tests directory. Each test constructs its own fresh application instance backed by an in-memory database, so tests are independent of one another and of the development database.

| Test file | Tests | What is verified |
|---|---|---|
| tests/test_auth.py | 5 | Successful login redirects to the correct role dashboard; a wrong password is rejected with the expected message; logout ends the session; stored password hashes differ from the plaintext and verify correctly; public registration accepts staff and technician roles but refuses to create an administrator. |
| tests/test_assets.py | 5 | An administrator can create an asset; duplicate asset tags are rejected instead of creating a second row; a staff member sees only the assets assigned to them and not another staff member's assets; a staff member is refused permission to delete an asset; two independently configured application instances keep their sessions and their data separate. |
| tests/test_tickets.py | 6 | A staff member can raise a ticket and is recorded as its creator, with the remote support identifier stored; an administrator can assign a ticket to a technician who really holds that role; a technician can advance their assigned ticket to In Progress; an illegal transition out of Resolved is refused; a technician can log maintenance against an asset; and the resolution rules refuse to resolve a ticket without adequate resolution notes. |

The suite is run with the command shown below. Because the tests exercise the application through its HTTP interface, they simultaneously verify the routing, the decorators, the validation and the persistence layer.

```sql
python -m pytest -q
```

The suite also served as a regression guard. When the ticket status-transition rules were tightened partway through the build, the existing tests immediately confirmed that the legal transitions still worked, which is exactly the value an automated suite is supposed to provide.

### 3.8  Software and Tools Used

During my training I made use of the following:

- Programming languages: Python, SQL, HTML, CSS and JavaScript.
- Web framework and libraries: Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-SocketIO, SQLAlchemy and Jinja2.
- Database: SQLite, together with the SQLite command-line client for inspecting tables and data during development.
- Front-end: Bootstrap, Bootstrap Icons, Chart.js and the Socket.IO client library.
- Editor: a text editor with Python language support and an integrated terminal.
- Version control: Git, with GitHub used to host the repository.
- Testing: pytest.
- Documentation: Markdown for the project README, and a word processor for the formal reports.
- Environment management: Python virtual environments and a .env file for configuration.

### 3.9  Skills and Knowledge Acquired

Through this work I acquired and strengthened the following skills:

- Web application development with Python and Flask, including the application factory pattern, blueprints and template inheritance.
- Relational database design and implementation — modelling entities, choosing primary and foreign keys, applying constraints and reasoning about cascade behaviour.
- Object-relational mapping with SQLAlchemy, including relationships, back-population and aggregate queries.
- Authentication and session management, and the difference between authentication, authorisation and ownership.
- Event-driven programming over WebSockets, including the reasoning about which clients should receive which events.
- Server-side validation and workflow enforcement — treating the client as untrusted and keeping the rules of the process in one place.
- Test-driven verification with pytest, including constructing isolated application instances per test.
- Reading and reasoning about an existing codebase, and documenting it accurately for someone who has never seen it.
- Time management, self-direction and the discipline of finishing and documenting work rather than leaving it partially complete.

---

## CHAPTER FOUR: CHALLENGES ENCOUNTERED

The training was productive, but it presented real difficulties. The most useful lessons came from the challenges rather than the parts that worked on the first attempt.

1. Evolving the database schema without a migration tool. The data model changed several times as the requirements became clearer: the account approval flags were added to the user table, eight resolution and support columns were added to the ticket table, and asset metadata such as brand, model, department and location was added to the asset table. Because the initial design did not set up a migration tool, there was no versioned path from the old schema to the new one. The workaround was to write reconciliation routines that run at application startup, inspect the existing tables and add any missing column. This solved the immediate problem but taught me why schema changes should be versioned from the first commit rather than patched in application code.
2. Enforcing the rules of the workflow on the server. It was straightforward to present a dropdown of ticket statuses, but presenting an option is not the same as permitting it. The first version allowed a ticket to be moved to any status from any status, which made the resolution record inconsistent — a ticket could be marked Resolved with no diagnostic steps recorded at all. Correcting this meant writing an explicit transition table, forcing any 'Unable to Resolve' outcome back to In Progress rather than allowing it to close the ticket, and refusing to resolve a ticket whose resolution notes were too short to be meaningful. The lesson was that a workflow is a set of rules, and rules belong on the server.
3. Authorising real-time events, which have no route decorator. The role-checking decorator protects HTTP routes, but a Socket.IO event handler is not a route and receives no such protection. My first implementation of the chat channel admitted any connected socket into any ticket room, which would have allowed one member of staff to read another's conversation by guessing a ticket number. The fix was to repeat the ownership check inside the socket handlers, to admit a socket to a ticket room only if the authenticated user is the ticket's creator or its assigned technician, and to refuse messages once a ticket is resolved or closed.
4. Understanding cascade behaviour and its risk. The relationship configuration was set to cascade deletes from a user to that user's assets, tickets, maintenance logs and notifications. This keeps the database tidy, but it also means that deleting a single user account silently removes every record attached to that person, including the history of work they performed. Reasoning carefully about which deletes should cascade and which should be refused was a lesson in the difference between referential tidiness and the preservation of history.
5. Testing role-scoped behaviour rather than only the happy path. It is easy to write a test that confirms an administrator can create an asset. It is harder, and more valuable, to write tests that confirm a staff member cannot delete one, that a staff member cannot see another staff member's equipment, and that an illegal status transition is refused. Writing those tests forced me to state the permission rules precisely enough to be able to assert them, and in doing so I found permission gaps I had not noticed in the code.
6. Working with a database engine that does not enforce everything. SQLite is convenient, but it does not enforce foreign keys unless the connection explicitly enables the constraint, and it has no native enumerated type. This meant that a great deal of data integrity that a server-based database would have provided for free had to be supplied by application code. Discovering that a value could be written to the database that the application would never itself produce changed how I thought about where validation should live.
7. Keeping the interface and the server in agreement. Several rules appear in two places: a field is conditionally required in JavaScript so the user gets immediate feedback, and it is required again on the server so the rule cannot be bypassed. Keeping the two in step, and remembering that only the server-side copy is a real control, took deliberate effort.
8. Documenting accurately. Writing this report required reading my own code critically rather than from memory, and several things I believed were true turned out not to be — a dependency listed in the requirements file that was never initialised, two templates no route ever renders, and a protection that was configured off. Documenting a system honestly is itself a form of review.

---

## CHAPTER FIVE: OBSERVATIONS AND CONTRIBUTIONS

### 5.1  Observations

- I observed that a large part of professional software work is deciding what to record. The value of NETSCOPE does not come from the interface; it comes from the fact that the diagnostic steps, the actions taken, the resolution and the cost of maintenance are captured while they are still known.
- I observed that authorisation is not a single decision but three separate ones. Confirming that a user is logged in, confirming what role they hold, and confirming that the particular record belongs to them are distinct checks, and a system that performs only the first two is not secure.
- I observed that a workflow is only real if the server enforces it. Every rule that lived only in the interface was eventually circumvented during testing.
- I observed that writing tests changes the design. Being forced to write an assertion about what a permission rule means made vague rules precise, and exposed cases that had not been considered.
- I observed that a monolith is not the same as an unstructured program. Grouping the code by role kept a single deployment unit readable, and the discipline of layers was what made the codebase navigable rather than the number of services.
- I observed that configuration decisions carry as much risk as code. A single setting left in its development value can remove a protection that the application's own code is carefully preparing for.
- I observed that documentation is a review technique. Describing the system to someone who has never seen it revealed inconsistencies that reading the code line by line had not.

### 5.2  Contributions

- I designed and built NETSCOPE end to end — the requirements, the data model, the authorisation model, the route layer, the templates, the client-side behaviour and the test suite.
- I designed the six-table relational schema, including its keys, constraints and cascade behaviour, and wrote the accompanying database report.
- I implemented the ticket lifecycle, including the server-side transition rules and the requirement that a meaningful resolution be recorded before a ticket can be resolved.
- I implemented the private per-ticket messaging channel and the live administrator notification system using WebSockets, with ownership enforced inside the event handlers.
- I implemented asset lifecycle management, including assignment to staff members and the per-asset maintenance log.
- I built the administrative dashboards and reports, including the aggregate queries behind the charts.
- I wrote the automated test suite of sixteen tests and used it as a regression guard while the workflow rules were tightened.
- I wrote the project README, the project documentation and this report, and in doing so identified the implementation gaps listed in section 5.3.

### 5.3  Limitations of the Current Implementation Identified During the Project

The following limitations were found while documenting and reviewing the finished system. They are recorded here rather than omitted, because an accurate account of a system includes what it does not yet do properly.

| # | Limitation | Severity |
|---|---|---|
| 1 | Request-token (CSRF) protection is switched off in the configuration, and the production configuration inherits that setting. The application generates and transmits tokens correctly; the enforcement flag is simply not enabled. This is the most serious issue in the current codebase. | Critical |
| 2 | The secret key used to sign sessions falls back to a fixed, publicly known development value if the environment variable is not set, which would make session cookies forgeable in a deployment that forgot to set it. | Critical |
| 3 | The session and remember-me cookies are not marked as secure, so they would be transmitted over plain HTTP. This must be enabled alongside HTTPS. | Major |
| 4 | The SQLite database file, an older backup of it, compiled bytecode and a leftover test page are committed to the version-control repository, and there is no ignore file to prevent it. The database contains real user rows and password hashes, so this is both a security exposure and a source of confusion, since a clone of the repository starts with someone else's data. | Critical |
| 5 | Schema changes are applied by reconciliation routines that run at application startup rather than by versioned migrations. A migration library is declared in the requirements file but is never initialised, so the declared dependency is unused. | Major |
| 6 | Business logic sits inside the view functions with no service layer beneath it, so rules such as the ticket transition table can only be tested through the HTTP interface. This makes the rules harder to verify in isolation and duplicates validation between routes. | Major |
| 7 | The account approval workflow cannot be reached through normal use. The approval flag defaults to true and registration sets it to true explicitly, so no account is ever created in the pending state the login page handles. | Minor |
| 8 | Two templates, an equipment-request page for staff and a matching administrator page, are present in the project but are not referenced by any route, so they can never be rendered. | Minor |
| 9 | There is no foreign key from a ticket to an asset. The relationship between a reported fault and the device it concerns is instead guessed by searching the ticket title and description for words such as 'device', 'computer' and 'laptop'. This means the link is unreliable and cannot be queried, which is a data-modelling gap rather than a cosmetic one. | Major |
| 10 | The values for ticket status, priority, category, support type, resolution outcome and user role are stored as free text and validated only in application code, with no database-level constraint. A direct write to the database, or a future code path that skips validation, can produce values the application does not understand. | Major |
| 11 | There are no indexes on the columns the dashboards filter and count on most heavily, including ticket status, technician, creator, asset status, asset owner and notification recipient. This is harmless at the current data volume but would become the first bottleneck as the system grows. | Minor |
| 12 | Maintenance costs are stored as floating-point numbers. Money should be stored as an exact decimal type, or as an integer number of the smallest currency unit, because floating-point arithmetic accumulates rounding error over time. | Major |
| 13 | Timestamps are written as offsets-aware values but persisted without the offset, so all stored times are effectively naive. This is consistent as long as the application is assumed to operate in a single time zone, but it cannot be relied upon otherwise. | Minor |
| 14 | There is no pagination on the ticket, asset or user lists. Every list loads entirely, which is acceptable at the current scale but will not remain so. | Minor |
| 15 | One unused import remains in the application factory. This is cosmetic on its own, but unused imports are worth removing because they mislead the reader about what a module depends on. | Minor |

Findings are graded as Critical when they expose data or allow a security control to be bypassed, Major when they affect correctness, maintainability or scale, and Minor when they are cosmetic or have no effect at the present data volume.

---

## CONCLUSION

My industrial training attachment was a genuinely useful and demanding period of work. I moved from studying software engineering as a subject to designing, building, testing and documenting a complete web application that addresses a real operational problem.

The main software I built, NETSCOPE, turned an informal support process into a system of record. It gives an organisation a single place in which support requests are raised, assigned, worked on and closed, in which the diagnostic steps and the resolution of every fault are preserved, and in which every item of equipment owned by the organisation is known, tracked and accounted for. Building it required me to work across the full stack: requirements analysis, database design, backend development, authorisation modelling, front-end implementation, real-time event handling, automated testing and documentation.

The most valuable lessons were not about any single library. They were about where responsibility belongs. Rules must be enforced on the server, because the interface is a convenience and not a control. Authorisation is three separate questions and not one. Schema changes should be versioned from the first commit, because retrofitting that discipline is expensive. And a system is not properly understood until it has been described in writing to someone who has never seen it, which is how the security and design gaps in section 5.3 were found.

I am confident that the technical knowledge, the engineering judgment and the professional working habits gained during this attachment will serve me well in my remaining studies and in my career, and I am grateful for the opportunity to have taken part in the scheme.

## RECOMMENDATIONS

On the basis of my training, I make the following recommendations.

### To the Organisation

- The request-token protection that is currently switched off should be enabled before the system is exposed to real users, and the secret key should be supplied through the environment with no fallback value.
- The database file and its backup should be removed from version control and an ignore file added, since the repository currently distributes real account data.
- Versioned database migrations should be adopted immediately, so that changes to the schema are recorded and reversible instead of being applied by application code at startup.
- A ticket should be linked to an asset by a proper key rather than by searching the text of the complaint, so that equipment fault history can be reported accurately.
- Money should be stored using an exact decimal type rather than a floating-point type.
- As the volume of records grows, indexes should be added to the columns that the dashboards and queues filter on, and the lists should be paginated.
- The workflow rules should be extracted from the view functions into a service layer so that they can be tested directly and reused.

### To the Institution

- Students should be encouraged to take placements in which they carry real responsibility for a deliverable, because growth comes from ownership rather than observation.
- Version control, testing, database design and technical documentation should be taught early and treated as core professional skills rather than optional extras, since they are used every day in practice.
- Orientation for students proceeding on attachment should set clear expectations about professional conduct, record keeping and the standard of work expected.
- The department should strengthen the monitoring and support provided to students on remote and hybrid placements, which increasingly reflect how the industry operates.

### To Future Students

- Keep the log book current rather than reconstructing it at the end, and include diagrams — the act of drawing the system is itself a design review.
- Set up version control, a migration tool and an ignore file on the first day of a project, not after the first schema change.
- Write tests for the permission rules and the failure paths, not only for the features that work.
- Read the finished code critically before writing the report. Several of the most important findings in this report came from that reading.

## REFERENCES

- Industrial Training Fund (ITF). Students Industrial Work Experience Scheme (SIWES) guidelines. Available at: https://www.itf.gov.ng
- Flask documentation. Available at: https://flask.palletsprojects.com
- Flask-SQLAlchemy documentation. Available at: https://flask-sqlalchemy.palletsprojects.com
- Flask-Login documentation. Available at: https://flask-login.readthedocs.io
- Flask-SocketIO documentation. Available at: https://flask-socketio.readthedocs.io
- SQLAlchemy documentation. Available at: https://docs.sqlalchemy.org
- SQLite documentation. Available at: https://www.sqlite.org/docs.html
- Jinja2 documentation. Available at: https://jinja.palletsprojects.com
- Werkzeug security utilities documentation. Available at: https://werkzeug.palletsprojects.com
- Bootstrap documentation. Available at: https://getbootstrap.com/docs
- Chart.js documentation. Available at: https://www.chartjs.org/docs
- Socket.IO client documentation. Available at: https://socket.io/docs
- pytest documentation. Available at: https://docs.pytest.org
- OWASP Foundation. Cross-Site Request Forgery Prevention Cheat Sheet. Available at: https://cheatsheetseries.owasp.org
- OWASP Foundation. Authentication Cheat Sheet. Available at: https://cheatsheetseries.owasp.org
- Martin, R. C. (2008). Clean Code: A Handbook of Agile Software Craftsmanship. Prentice Hall.
- Fowler, M. (2002). Patterns of Enterprise Application Architecture. Addison-Wesley.

---

## APPENDIX A: ROUTE AND ENDPOINT REFERENCE

The table below lists every route in the application, the role permitted to reach it and its purpose. Routes marked as public do not require a session.

| Method | Path | Permitted role | Purpose |
|---|---|---|---|
| GET | / | Public | Landing page, or redirect to the role dashboard if already authenticated. |
| GET | /dashboard | Any authenticated | Redirect to the dashboard matching the user's role. |
| GET, POST | /auth/login | Public | Authenticate a user by username or email. |
| GET, POST | /auth/register | Public | Register a staff or technician account. |
| POST | /auth/logout | Any authenticated | End the session. |
| GET | /auth/profile | Any authenticated | Display the current user's profile. |
| GET | /admin/dashboard | Administrator | Key metrics, charts and pending tickets. |
| GET | /admin/assets | Administrator | List all assets. |
| GET, POST | /admin/assets/new | Administrator | Register a new asset. |
| GET | /admin/assets/<id> | Administrator | Asset detail with its maintenance history. |
| GET, POST | /admin/assets/<id>/edit | Administrator | Edit an asset. |
| POST | /admin/assets/<id>/delete | Administrator | Delete an asset. |
| POST | /admin/assets/<id>/assign | Administrator | Issue an asset to a staff member. |
| POST | /admin/assets/<id>/unassign | Administrator | Return an asset to the pool. |
| GET | /admin/users | Administrator | List all user accounts. |
| GET, POST | /admin/users/new | Administrator | Create a user account. |
| POST | /admin/users/<id>/approve | Super administrator | Approve a pending account. |
| GET | /admin/tickets | Administrator | List and filter all tickets. |
| GET | /admin/tickets/<id> | Administrator | Ticket detail and administration panel. |
| POST | /admin/tickets/<id>/assign | Administrator | Assign a ticket to a technician. |
| POST | /admin/tickets/<id>/status | Administrator | Override a ticket's status. |
| POST | /admin/notifications/read | Administrator | Mark all notifications as read. |
| GET | /admin/reports | Administrator | Assets, tickets, workload and maintenance reports. |
| GET | /staff/dashboard | Staff | Personal ticket and asset summary. |
| GET | /staff/assets | Staff | Assets assigned to the current user. |
| GET, POST | /staff/tickets/new | Staff | Raise a support ticket. |
| GET | /staff/tickets | Staff | Tickets raised by the current user. |
| GET | /staff/tickets/<id> | Staff | Ticket detail and conversation. |
| GET | /technician/dashboard | Technician | Workload summary and alerts. |
| GET | /technician/queue | Technician | All tickets assigned to the current user. |
| GET | /technician/tickets/<id> | Technician | Ticket detail and resolution form. |
| POST | /technician/tickets/<id>/start-work | Technician | Move an open ticket to In Progress. |
| POST | /technician/tickets/<id>/status | Technician | Save resolution details and update status. |
| GET, POST | /technician/maintenance | Technician | Log maintenance work against an asset. |
| GET, POST | /tickets/<id>/messages | Ticket creator or assigned technician | Read or send a message in the private ticket conversation. |

The application also exposes the following Socket.IO events:

| Event | Direction | Purpose |
|---|---|---|
| join_admin | Client to server | Admit an administrator's socket to their private notification room. |
| join_ticket_chat | Client to server | Admit a participant's socket to a ticket's conversation room, after the server verifies ownership. |
| send_ticket_message | Client to server | Send a message to a ticket conversation. |
| new_ticket_notification | Server to client | Notify an administrator that a ticket has been created. |
| ticket_message_received | Server to client | Deliver a message to the other participants in a ticket conversation. |

Two management commands are also provided:

```sql
flask --app run.py init-db        # create the database tables
flask --app run.py init-db --drop # drop and recreate the tables
flask --app run.py create-admin   # create the first administrator account
```
