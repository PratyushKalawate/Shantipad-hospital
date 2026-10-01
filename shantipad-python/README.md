# Shantipad Hospital Website and Python Admin

A six-page website with English, Hindi and Marathi content, backed by Django 5.2 and SQLite. Appointments remain phone-based. No patient records, patient login, online booking, or payment processing are implemented.

## Start locally

Install Python 3.12 or newer. Open a terminal in this folder and run:

```sh
python3 start.py
```

The first run creates a virtual environment, installs dependencies, creates the database, imports the supplied hospital content, and asks you to create an admin username and password. No shared or default admin password is included.

- Website: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

On Windows use `python start.py`. Keep the terminal open while using the local website.

## Edit the website

Log in at `/admin/`. Edit a record and select Save, then refresh the public website.

- Hospital settings: address, introduction, contact information, emergency availability, logo, hero photo, and private certification records for authorized administrators.
- Doctors: names, qualifications, experience, biography, consultation notes, registration details and portrait upload.
- Services: pediatric or dental treatments, translated descriptions, order and visibility.
- Facilities: hospital facilities, translations, order and visibility.
- Partners: cashless schemes, insurers and other empanelled partners.
- Appointment phones: the numbers shown by Call to book.
- Opening hours: labels, times and lunch-break notes in all three languages.
- Frequently asked questions: questions and answers in all three languages.
- Page text: headings, labels and supporting copy. Keep the existing key unchanged. Use plain text; a newline creates a line break.
- Users and Groups: separate staff accounts and permissions. Only give a user the sections they should edit.

Blank Hindi or Marathi translations fall back to English. Unpublished records do not appear on the public API. Images accept JPEG, PNG and WebP up to 5 MB; certificates accept PDF up to 10 MB. Public image uploads replace fallback asset URLs. Certificate files and certification marks use separate private storage and can only be downloaded from the admin by users with hospital-view or hospital-change permission. When changing the hero photo, also update `heroImageAlt` and `heroImageCaption` in Page text.

## Confirmed content

- Dr. Akhilesh Kalawate: MBBS, DCH (Gold Medal), 15 years of experience and DNB registrar experience. DNB is not presented as an awarded qualification.
- Dr. Sonal Akhilesh Kalawate: BDS, from the supplied brochure.
- Address: Murarka College Road, Shegaon, Buldhana 444203, Maharashtra, confirmed by the client.
- OPD every day, including Sunday: 9:30 AM to 4 PM and 6 PM to 8 PM. Lunch break: noon to 1 PM.
- Emergency availability: 24 hours, separate from routine consultations.
- Pediatric/dental services and facilities are transcribed from the supplied service brochure. No treatment advice is added.
- The latest empanelment list and pictured list are included; ICICI Lombard is spelled using the brochure. Care/Religare and Plunes-related entries are grouped for readability. Eligibility and approval must be confirmed with the hospital.
- Private certification record: NABH Entry-Level Certified (SHCO), certificate PESHCO-2026-12586, valid 2026-08-04 through 2028-08-03. The supplied certificate names Shantipad Hospital and scopes Dentistry, Paediatrics and Blood Transfusions Services.

Certification details, the certificate PDF, and the certification mark are private administration records. They are excluded from the public content API and website. The former public PDF and mark URLs return 404. Updating these records in the admin does not publish them.

Individual doctor portraits, registration numbers, contact email and a Google Maps pin are still optional missing information. Google Maps appears once its link is entered. The family hero photograph remains visibly labeled as illustrative stock.

## Development

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_content
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 127.0.0.1:8000
.venv/bin/python manage.py test
```

Content is served from the read-only `GET /api/content/` endpoint. The frontend escapes content and accepts only HTTP(S) asset links. Admin writes use Django authentication, model permissions and CSRF protection. Re-running the seed command preserves administrator changes.

Main files: `cms/models.py`, `cms/admin.py`, `cms/views.py`, `seed.json`, and `frontend/app.js` / `frontend/styles.css`. The admin is Django's existing administration interface, branded for Shantipad.

## Deployment later

This project has not been hosted. The included development server is local-only.

For production set `DJANGO_DEBUG=0`, a unique `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS`; configure HTTPS, a production WSGI/ASGI server, login throttling, backups, and a protected operational environment. Collect static files with `manage.py collectstatic` for WhiteNoise. Serve public media separately with a server that cannot execute uploads; Django serves media automatically only in development. Verify reverse-proxy settings for HTTPS and run `manage.py check --deploy`.

Back up `db.sqlite3`, `media/`, and `private/`. Never expose `private/` through the web server or include it in static-file directories. A production database can replace SQLite in `config/settings.py`. The ZIP excludes local credentials, database, virtual environments and temporary test files. Its seed data recreates the initial content, including the privately stored client certificate for administrator access.

Keep the current noindex setting until the content and translations are approved for public launch.

## Sources and assets

The certificate and NABH marketing guidance were supplied by the client. The certificate and certification mark are kept in `private/certification/`, outside public assets and public media. The hospital logo and service brochure remain in `frontend/assets/`.

Stock family photograph: Rashmi Kalburgie on Unsplash, https://unsplash.com/photos/happy-mother-and-baby-smiling-on-a-clean-white-surface-acszEuL2AdU .

External hero imagery and Google Fonts require internet access. Lucide icons are bundled locally with their license.

Django documentation: https://docs.djangoproject.com/en/5.2/ and deployment checklist https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ .
