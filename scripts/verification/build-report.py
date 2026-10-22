#!/usr/bin/env python3
"""Assemble the ten-section submission from source and genuine captured evidence."""
import html,json,re,textwrap
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.etree import ElementTree as ET
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Preformatted,Image,LongTable,TableStyle,PageBreak
root=Path(__file__).resolve().parents[2];out=root/'docs/evidence/current'
facts=json.loads((out/'database-facts.json').read_text());scenario=json.loads((out/'demonstrations.json').read_text());bench=json.loads((out/'benchmark.json').read_text())
xml=ET.parse(out/'pytest.xml').getroot();suites=[xml] if xml.tag=='testsuite' else list(xml.iter('testsuite'))
tests=sum(int(x.get('tests','0')) for x in suites);failures=sum(int(x.get('failures','0'))+int(x.get('errors','0')) for x in suites)
browser=(out/'browser-tests.txt').read_text();match=re.search(r'(\d+) passed',browser);browsers=int(match.group(1)) if match else 0
if failures or not tests or not browsers:raise SystemExit('Report requires a passing captured verification run')
when=datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %B %Y, %H:%M IST')
# Testing documentation always derives counts from real machine-readable output.
testing=f'''# Verification results

Generated {when}. Python tests ran against accessledger_test; browser tests use accessledger_test_browser. Original accessledger database is never a test target.

- Python: **{tests} tests, {failures} failures/errors**. Full test names and output: evidence/current/pytest.txt; machine-readable results: pytest.xml.
- Browser: **{browsers} passing tests**. Full output: evidence/current/browser-tests.txt. Tests exercise all five connected operations, six pages, mobile navigation, browser errors and delayed-response request consistency.
- TypeScript and production Vite build: executed successfully; output in evidence/current/frontend-build.txt.
- Database: actual schema/row counts/routines in database-facts.json; all query outputs in sql-output.txt; independent restricted-login ALLOW → revoke → DENY in demonstrations.json.
- Standalone SQL installation was also executed on accessledger_test_sql: eight domain tables, 120 events and the measured index; output: evidence/current/sql-only-install.txt.
- Original evidence SHA-256 and preserved database counts: evidence/current/preservation.json.
- Performance: {bench['events']:,} actual evaluated events, five measured plans per query/configuration, captured in benchmark.json and indexing.md.
- Screenshots: six live pages, actual ALLOW/DENY outcomes and mobile view in evidence/current/*.png. These use the live demo; screenshot capture adds real evaluation events.

The Python suite includes 39 retained constraint tests, authorization/default-deny/retention/report tests, eleven two-connection concurrency schedules, and real HTTP integration tests. Fault injection covers audit insertion failure and a deferred failure at COMMIT, proving the API never returns a successful ALLOW for an uncommitted audit event. The database-unavailable response is tested using a real failed connection.

A browser regression first failed while employee/resource/action selectors remained editable during a delayed evaluation response. Disabling selectors while pending fixes misattribution of a returned decision. The independent code review found no critical SQL/API defect; this important UI finding and a legacy evidence-overwrite risk were corrected.

Limitations: Docker Compose is supplied but unexecuted because Docker WSL integration is unavailable. Local PostgreSQL 16.15, Python 3.12 and Node 22 LTS were used instead. Browser tests ran headless Chromium on Linux; other browsers and a formal WCAG audit were not performed. Test output includes a Starlette/httpx deprecation warning and Playwright's NO_COLOR/FORCE_COLOR warning; neither is hidden or counted as a failure. Benchmark timings are local warm-cache observations, not production throughput guarantees. Student identity fields remain for the student to complete. No public deployment or remote push was performed.
'''
(root/'docs/testing.md').write_text(testing)
counts='\n'.join(f'| {k.upper()} | {v} |' for k,v in facts['seed_counts'].items())
queries=(root/'database/queries/010_required_catalog.sql').read_text();sqlout=(out/'sql-output.txt').read_text()
qblocks=[]
for m in re.finditer(r"\\echo '(Q\d\d [^']+)'\n([^\\]+?;)(?=\n\\echo|\s*$)",queries,re.S):
    label,sql=m.groups();marker=re.search(r'^'+re.escape(label)+r'\n',sqlout,re.M)
    fragment=sqlout[marker.end():] if marker else ''
    nextmark=re.search(r'^Q\d\d |^SOURCE:',fragment,re.M)
    if nextmark:fragment=fragment[:nextmark.start()]
    lines=fragment.strip().splitlines();sample='\n'.join(lines[:7]);total=next((line.strip() for line in reversed(lines) if re.search(r'\(\d+ rows?\)',line)), 'See full captured output')
    qblocks.append(f"### {label}\n\n```sql\n{sql.strip()}\n```\n\nActual output excerpt ({total}):\n\n```text\n{sample}\n```\n")
assert len(qblocks)==15,len(qblocks)
report=f'''# AccessLedger

A Role-Based Access Control and Security Audit Management System

Academic submission assembled {when}. Evidence timestamps remain explicitly labelled UTC where captured.

## 1. Project Title and Team/Student Details

- Project: AccessLedger
- Institution: VIT Vellore
- Theory course: BCSE302L — Database Systems
- Laboratory: BCSE302P — Database Systems Lab
- Student name(s): [TO BE SUPPLIED BY STUDENT]
- Registration number(s), faculty and review dates: [TO BE SUPPLIED BY STUDENT]

Authority is the user-supplied master requirements and approved plan. The four referenced faculty PDFs were not present; no additional requirements or exact PDF claims are invented. The earlier prototype database and evidence are preserved separately.

## 2. Introduction and Problem Statement

Organizations need a consistent answer to who may perform an action on a protected resource, and a reliable account of attempted access. Individually managing each employee's permissions becomes difficult as responsibilities and resources grow. AccessLedger represents employees, departments, roles, resource actions and assignments in related PostgreSQL relations. Active role paths grant access; all other valid requests are denied and logged.

The primary deliverable is the database: relational integrity, controlled PL/pgSQL business operations, transactional audit recording, concurrency correctness and inspectable SQL. The application makes these concepts demonstrable through connected workflows. It does not enforce access on production resources.

Architecture: React/TypeScript/Vite/Tailwind → FastAPI/Pydantic → SQLAlchemy/Psycopg → PostgreSQL 16. Migrations execute canonical SQL; migration metadata is separate infrastructure. No paid/external service is required.

## 3. Functional Requirements

Register and edit departments/employees; disable users; define and activate/deactivate roles/resources; define unique resource actions; assign/revoke user roles and role permissions; retrieve distinct effective permissions; evaluate access and persist one event; explore filtered/paginated history and aggregate reports.

ALLOW requires an active existing user, existing permission, active associated resource and an active assigned role granting that permission. Valid-reference reason precedence is USER_DISABLED, RESOURCE_INACTIVE, NO_ACTIVE_ROLE, PERMISSION_NOT_GRANTED, then PERMISSION_GRANTED. Invalid user is checked first; invalid user/permission returns an unlogged DENY with a null audit identifier. The browser/API never supplies an authoritative decision or reason.

Included scope is a single trusted local organization. No role inheritance, direct user permissions, federation, SSO, multi-tenancy, approvals, physical access or AI analysis is included. Administrative authentication and production deployment are outside this demonstration.

## 4. ER Diagram

![Crow's Foot model](er-diagram.png)

The diagram is generated using the live eight-table catalog. Double bars mean exactly one; circle/fork means zero or many. Each employee belongs to exactly one department. USER_ROLE and ROLE_PERMISSION implement independent many-to-many relationships. ACCESS_LOG references a permission, which determines its resource, avoiding a redundant resource FK in the event.

The editable Mermaid diagram, vector SVG and candidate-key details are delivered alongside this report.

## 5. Relational Schema

{(root/'docs/relational-schema.md').read_text().split('# Relational schema',1)[1].strip()}

Normalization analysis: all eight tables are 1NF and 2NF. The first seven satisfy 3NF and BCNF under the listed business dependencies. ACCESS_LOG deliberately retains reason_code → decision: the determinant is not a superkey and decision is not prime, so it violates both 3NF and BCNF. A generated column prevents inconsistent pairs without removing the dependency. Full FDs and candidate keys are documented in normalization.md; no false full-schema 3NF claim is made.

## 6. Table Creation and Constraints

DDL is inspectable in database/schema/001_core_schema.sql, executed by Alembic revision 001. The decision/time index is revision 002. Exactly eight public base tables exist; Alembic version metadata is in infrastructure.

Primary keys include composite junction keys; candidate keys use NOT NULL + UNIQUE. All FKs use ON DELETE RESTRICT. CHECK constraints constrain user status and audit reason. Defaults activate users/roles/resources and timestamp assignments. Identity keys distinguish repeated events. Email is normalized before uniqueness. Required decision is generated from the controlled reason.

Actual fresh seed counts captured from {facts['database']}:

| Relation | Rows |
|---|---:|
{counts}

The seed includes disabled users, inactive roles/resources, multiple roles, no-role users, an empty permission role, repeated evaluations and a verified revocation history. Events are produced by evaluate_access, not fabricated decision inserts. Logical relationships are repeatable; event timestamps reflect actual execution.

## 7. SQL Queries and Outputs

The following fifteen queries were executed on the final schema. Excerpts below are copied from actual psql output; the complete unedited output is evidence/current/sql-output.txt. User/department/permission parameters are selectable with psql variables. Additional join, aggregation, subquery and view exercises are retained and executed. The DML demonstration registers, renames and deletes an unused department inside a rolled-back transaction, using a legitimate core entity rather than an extra exercise table.

{''.join(qblocks)}

## 8. Procedures, Functions, Cursor, and Triggers

assign_user_role validates existing active user/role and inserts a unique assignment; revoke_user_role removes the current assignment while preserving old events. grant_role_permission and revoke_role_permission control grants. Additional management and activation routines cover every application mutation path.

evaluate_access obtains a shared transaction advisory lock, checks policy, inserts one event for valid references and returns decision, reason, log ID and timestamp. It is VOLATILE and reads policy after waiting under READ COMMITTED. get_effective_permissions returns distinct current permissions excluding disabled/inactive entities.

generate_access_activity_summary explicitly OPENs a cursor over users, FETCHes each user, calculates total/allowed/denied counts, RETURN NEXTs the report row, and CLOSEs the cursor. It includes zero-event users and creates no report table.

Audit UPDATE/DELETE/TRUNCATE triggers reject modification even for a role allowed to reach them. The application login also lacks these privileges. The permission-identity trigger rejects resource/action changes after a permission is logged. Direct application INSERT into ACCESS_LOG is denied, so clients cannot forge PERMISSION_GRANTED. Safe SECURITY DEFINER ownership/search paths and selective EXECUTE grants complete this boundary. Superuser bypass remains possible and is explicitly not called tamper-proof logging.

Concurrency uses shared advisory transaction lock (302,8) for evaluations and exclusive mode for every controlled policy mutation. READ COMMITTED is enforced. This simple global lock sacrifices unrelated policy-write concurrency in return for a clear auditable protocol; owner maintenance must follow the same protocol. Separate API transactions avoid lock upgrades and commit before returning success.

## 9. Real-World Transaction Demonstrations

Five connected operations are executed using the actual application database login: employee registration, role assignment, permission assignment, evaluation and role revocation followed by reevaluation. API/SQL/table mappings and verification queries are in demonstrations.md. The browser test independently executes the same connected workflow.

Actual controlled SQL demonstration:

```json
{json.dumps({k:v for k,v in scenario.items() if k!='retained_history'},indent=2,default=str)}
```

Both retained joined events are present in demonstrations.json. Removing one of multiple granting roles need not deny access; the demonstration uses a sole-provider role.

Validation results: **{tests} Python tests passed with {failures} failures/errors; {browsers} browser tests passed**. The suite covers constraints, application-login privileges, owner-level triggers, invalid references, repeated attempts, distinct permissions, rollback and injected audit insertion/commit failure. Eleven two-connection tests prove both lock orders across five mutation types and shared simultaneous evaluations. Full commands/results are captured rather than inferred from source.

Performance uses {bench['events']:,} genuine evaluated events on a separate database. Five EXPLAIN (ANALYZE, BUFFERS) runs per configuration show latest-denial median {bench['queries']['latest_denials']['before']['median_execution_ms']:.3f} ms before and {bench['queries']['latest_denials']['after']['median_execution_ms']:.3f} ms after the decision/time/log_id index. Other paths use existing indexes; minor timing differences are not attributed to the new index. Full plans and all timings are retained in benchmark.json.

![Live database-backed dashboard](evidence/current/dashboard.png)

![Actual allowed evaluation](evidence/current/access-allow.png)

![Actual denied evaluation](evidence/current/access-deny.png)

![Live audit explorer](evidence/current/audit.png)

## 10. Conclusion

AccessLedger demonstrates a relational RBAC authorization engine with transactional decision recording and historical retention, backed by inspectable SQL and real integration/concurrency evidence. The API and six-page interface support practical management and access/audit workflows without replacing mandatory database routines with application code.

Reproduction: follow README.md to create a Python environment, install pinned dependencies, bootstrap local PostgreSQL/Node, migrate/seed accessledger_demo and run scripts/dev.sh. Run scripts/verification/run-all.sh for disposable tests, executed SQL, the benchmark and report regeneration. Screenshot capture is a separate explicit live-demo action. No original database reset, remote push or public deployment is performed.

Limits: joined labels are current values, not historical snapshots; policy-change provenance is not stored. Local administrative authentication is outside scope. Docker Compose is provided but unexecuted on this host. Tests use Linux Chromium; other browsers and a formal accessibility audit are not claimed. Benchmark timing is local evidence. Student identity fields must be completed by the student. See requirements.md for the full requirement-to-evidence map and testing.md for warnings and scope limits.
'''
(root/'docs/final-report.md').write_text(report)
# Printable PDF with local embedded fonts, real diagram/screenshots, complete SQL excerpts.
fontdir=Path('/usr/share/fonts/truetype/dejavu')
for name,file in [('Body','DejaVuSans.ttf'),('BodyBold','DejaVuSans-Bold.ttf'),('Code','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold')
styles=getSampleStyleSheet()
for key in ['Normal','BodyText']:styles[key].fontName='Body';styles[key].fontSize=9;styles[key].leading=14
for key,size in [('Title',24),('Heading1',19),('Heading2',14),('Heading3',11)]:styles[key].fontName='BodyBold';styles[key].fontSize=size;styles[key].leading=size+6
code_style=ParagraphStyle('CodeStyle',fontName='Code',fontSize=6.5,leading=9,spaceAfter=10,backColor=colors.HexColor('#f5f7fb'),borderPadding=6)
flow=[];lines=report.splitlines();i=0
while i<len(lines):
    line=lines[i];i+=1
    if not line.strip():continue
    if line.startswith('```'):
        block=[]
        while i<len(lines) and not lines[i].startswith('```'):block+=textwrap.wrap(lines[i],width=105,replace_whitespace=False,drop_whitespace=False) or [''];i+=1
        i+=1;flow.append(Preformatted('\n'.join(block),code_style));continue
    image=re.match(r'!\[([^]]*)\]\(([^)]+)\)',line)
    if image:
        path=root/'docs'/image.group(2)
        if not path.exists():raise FileNotFoundError(path)
        from PIL import Image as PILImage
        with PILImage.open(path) as im:w,h=im.size
        scale=min(500/w,650/h);flow.append(Image(str(path),width=w*scale,height=h*scale));flow.append(Paragraph(html.escape(image.group(1)),styles['Normal']));flow.append(Spacer(1,12));continue
    if line.startswith('|'):
        rows=[line]
        while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
        cells=[]
        for row in rows:
            if re.match(r'^\|[\s:|\-]+\|$',row):continue
            cells.append([Paragraph(html.escape(c.strip()),styles['Normal']) for c in row.strip('|').split('|')])
        n=len(cells[0]);table=LongTable(cells,colWidths=[500/n]*n,repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf3fc')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#dce4ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));flow.append(table);flow.append(Spacer(1,12));continue
    heading=re.match(r'^(#{1,3}) (.*)',line)
    if heading:
        level=len(heading.group(1))
        if level==2 and re.match(r'(4|7|8|9|10)\.',heading.group(2)):flow.append(PageBreak())
        flow.append(Paragraph(html.escape(heading.group(2)),styles[{1:'Title',2:'Heading1',3:'Heading3'}[level]]));continue
    text=html.escape(line)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'`([^`]+)`',r'\1',text)
    if text.startswith('- '):text='• '+text[2:]
    flow.append(Paragraph(text,styles['Normal']));flow.append(Spacer(1,6))
def footer(canvas,doc):
    canvas.setFont('Body',7);canvas.setFillColor(colors.HexColor('#73839a'))
    canvas.drawString(45,25,'AccessLedger · BCSE302L / BCSE302P · VIT Vellore')
    canvas.drawRightString(A4[0]-45,25,f'Page {doc.page}')
doc=SimpleDocTemplate(str(root/'docs/final-report.pdf'),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=45,bottomMargin=45,title='AccessLedger — Database Systems Project',author='AccessLedger Project Team (identity to be supplied)')
doc.build(flow,onFirstPage=footer,onLaterPages=footer)
print(f'Built report: {tests} Python tests, {browsers} browser tests, 15 executed queries; Markdown and PDF.')
