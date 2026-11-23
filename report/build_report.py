from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Lab5_Kubernetes_Resources.pdf"
REPOSITORY = "https://github.com/DariaSide/lab5-kubernetes-resource-management"
RESULT = json.loads((ROOT / "artifacts" / "results" / "parallel-top10.json").read_text(encoding="utf-8"))
DATA_SHA256 = "3d6e5a9d060a6f25eba9e691a4d9afafad007b366abfae936bfbc6027bf657e3"

font_candidates = [
    Path("/Users/side/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf"),
    Path("/Users/side/Documents/Codex/2026-10-21/hdfs-xa0-x43e-mapreduce-rustfs-json/.venv/lib/python3.9/site-packages/matplotlib/mpl-data/fonts/ttf"),
]
font_dir = next(path for path in font_candidates if (path / "DejaVuSans.ttf").exists())
pdfmetrics.registerFont(TTFont("DejaVu", str(font_dir / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(font_dir / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuMono", str(font_dir / "DejaVuSansMono.ttf")))

NAVY = colors.HexColor("#173B57")
TEAL = colors.HexColor("#168A8A")
LIGHT = colors.HexColor("#DCECF3")
INK = colors.HexColor("#1D2730")
MUTED = colors.HexColor("#5C6973")
DARK = colors.HexColor("#14232E")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleRU", fontName="DejaVu-Bold", fontSize=25, leading=31, textColor=NAVY, spaceAfter=12))
styles.add(ParagraphStyle(name="SubRU", fontName="DejaVu", fontSize=11, leading=16, textColor=MUTED, spaceAfter=7))
styles.add(ParagraphStyle(name="H1RU", fontName="DejaVu-Bold", fontSize=17, leading=22, textColor=NAVY, spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name="H2RU", fontName="DejaVu-Bold", fontSize=12, leading=16, textColor=TEAL, spaceBefore=7, spaceAfter=6))
styles.add(ParagraphStyle(name="BodyRU", fontName="DejaVu", fontSize=9.3, leading=13.8, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name="SmallRU", fontName="DejaVu", fontSize=7.5, leading=10.5, textColor=INK))
styles.add(ParagraphStyle(name="TinyRU", fontName="DejaVu", fontSize=6.7, leading=9.0, textColor=INK))
styles.add(ParagraphStyle(name="MonoRU", fontName="DejaVuMono", fontSize=7.1, leading=10.0, textColor=colors.HexColor("#E8EEF2"), backColor=DARK, borderPadding=8, spaceAfter=8))
styles.add(ParagraphStyle(name="Callout", fontName="DejaVu-Bold", fontSize=10, leading=14, textColor=NAVY, backColor=LIGHT, borderPadding=9, spaceAfter=10))


def p(text: str, style: str = "BodyRU") -> Paragraph:
    return Paragraph(text, styles[style])


def code(text: str) -> Paragraph:
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    return p(safe, "MonoRU")


def table(rows, widths, style="SmallRU"):
    rendered = [[p(str(cell), style) for cell in row] for row in rows]
    result = Table(rendered, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F9FA")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8C6CF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D5DEE4"))
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("DejaVu", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9 * mm, "Лабораторная работа 5 - Kubernetes")
    canvas.drawRightString(192 * mm, 9 * mm, f"Страница {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
    topMargin=17 * mm, bottomMargin=18 * mm,
    title="Лабораторная работа 5. Управление ресурсами Kubernetes",
    author="Дарья Сидельникова",
)
doc.addPageTemplates(PageTemplate(id="main", frames=Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height), onPage=footer))
story = []

story += [
    Spacer(1, 16 * mm),
    p("Лабораторная работа 5", "TitleRU"),
    p("Управление ресурсами в Kubernetes", "TitleRU"),
    Spacer(1, 7 * mm),
    p("Пары навыков DevOps, RustFS, scheduling, priority и quota", "Callout"),
    p("Студент: Сидельникова Дарья Николаевна<br/>Группа: ИИИ-3-ИнжДан-1-2<br/>Преподаватель: Артём Галимьянов<br/>Дата выполнения: 23 ноября 2026 года", "SubRU"),
    Spacer(1, 5 * mm),
    p(f'<b>Репозиторий:</b> <link href="{REPOSITORY}" color="#168A8A">{REPOSITORY}</link>'),
    Spacer(1, 15 * mm),
    p("Цель", "H2RU"),
    p("Развернуть Kubernetes на локальном компьютере, упаковать расчёт пар навыков из ДЗ №3 в контейнер и исследовать requests/limits, OOMKilled, планирование при дефиците CPU, приоритетное вытеснение и квоты namespace. Перенести S3-совместимое хранилище RustFS из ДЗ №2 внутрь кластера и выполнить расчёт четырьмя параллельными задачами."),
]

story += [
    PageBreak(), p("1. Исходные данные и архитектура", "H1RU"),
    p("Вариант продолжает ДЗ №3 «DevOps-инженер». Использован тот же NDJSON без повторной подготовки, поэтому совпадение результата проверяется по навыкам и точным частотам, а не только по названиям."),
    table([
        ["Контрольный показатель", "Значение"],
        ["Вакансий", "5 158"],
        ["Строк с навыками", "3 534"],
        ["Размер входа", "1 628 741 байт"],
        ["Уникальных пар", "22 286"],
        ["SHA-256 входа", DATA_SHA256[:32] + "<br/>" + DATA_SHA256[32:]],
    ], [55 * mm, 107 * mm]),
    Spacer(1, 5 * mm), p("Компоненты", "H2RU"),
    table([
        ["Компонент", "Назначение"],
        ["kind / Kubernetes v1.34.0", "Одноузловой локальный кластер в Docker"],
        ["skill-pairs:lab5", "Python 3.12, boto3 и программа расчёта"],
        ["RustFS", "S3-совместимое хранилище внутри namespace lab5"],
        ["Indexed Job", "Четыре mapper Pod с индексами 0..3"],
        ["Reducer Job", "Слияние частичных Counter и публикация top-10"],
    ], [48 * mm, 114 * mm]),
    Spacer(1, 5 * mm),
    p("Поток данных: образ uploader загружает NDJSON в s3://hh-lake/input/devops_vacancies.ndjson; четыре mapper читают объект и выбирают строки по условию index mod 4; reducer читает четыре JSON-части из RustFS, суммирует счётчики и сохраняет итог."),
]

story += [
    PageBreak(), p("2. Образ и заявки на ресурсы", "H1RU"),
    p("Образ собирается из python:3.12-slim. Исходный файл включён только для первоначальной загрузки в RustFS; все расчётные Job получают вход через S3 API. Для воспроизводимости imagePullPolicy установлен в Never после загрузки образа в kind."),
    code("FROM python:3.12-slim\nWORKDIR /app\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY src/ ./src/\nCOPY data/devops_vacancies.ndjson ./data/\nENTRYPOINT [\"python\", \"-m\", \"src.worker\"]"),
    p("Requests и limits", "H2RU"),
    table([
        ["Запуск", "CPU request / limit", "Memory request / limit"],
        ["baseline", "100m / 1", "64Mi / 512Mi"],
        ["OOM test", "100m / 1", "32Mi / 64Mi"],
        ["selected limit", "100m / 1", "64Mi / 128Mi"],
        ["mapper x4", "100m / 1", "64Mi / 128Mi"],
        ["reducer", "100m / 1", "64Mi / 128Mi"],
    ], [48 * mm, 54 * mm, 60 * mm]),
    Spacer(1, 5 * mm),
    p("Планировщик учитывает request при выборе узла. Limit не резервирует ресурс для размещения: CPU ограничивается throttling, а превышение memory limit может завершить контейнер OOM kill."),
]

story += [
    PageBreak(), p("3. OOMKilled и подбор memory limit", "H1RU"),
    p("Сначала Job выполнен с большим пределом 512Mi. Программа измерила ru_maxrss внутри Linux-контейнера: пик составил <b>62,34 MiB</b>. Затем тот же расчёт запущен с memory limit 64Mi и контролируемой аллокацией 96Mi, имитирующей вход большего объёма."),
    code("job.batch/pairs-oom condition met\npod=pairs-oom-f26jw\nphase=Failed\nreason=OOMKilled\nexitCode=137\nLimits: memory: 64Mi"),
    p("Результат OOM", "Callout"),
    p("Контейнер остановлен ядром cgroup: Reason=OOMKilled, exitCode=137. Job имел backoffLimit: 0, поэтому после первого неуспеха получил состояние Failed."),
    p("Выбор рабочего предела", "H2RU"),
    p("Для обычного запуска выбран limit 128Mi. Это 2,05 от измеренного пика 62,34Mi и оставляет около 65,66Mi запаса на накладные расходы Python, boto3 и изменение размера входа. Повторный запуск завершился успешно с пиком <b>62,35 MiB</b> и теми же 22 286 уникальными парами. Таким образом, предел связан с измерением, а не выбран произвольно."),
    table([
        ["Сценарий", "Предел", "Пик", "Итог"],
        ["Измерение", "512Mi", "62,34Mi", "Complete"],
        ["Провокация", "64Mi", ">64Mi", "OOMKilled / 137"],
        ["Подобранный", "128Mi", "62,35Mi", "Complete"],
    ], [45 * mm, 34 * mm, 37 * mm, 46 * mm]),
]

story += [
    PageBreak(), p("4. RustFS внутри Kubernetes", "H1RU"),
    p("S3-хранилище из ДЗ №2 перенесено из docker-compose в StatefulSet. Service rustfs предоставляет стабильное имя rustfs.lab5.svc:9000. Учётные данные хранятся в Secret, адрес и ключ объекта - в ConfigMap. Для локальной лабораторной данные размещены в emptyDir; для постоянного кластера его следует заменить PVC."),
    code("NAME       READY   STATUS    RESTARTS\nrustfs-0   1/1     Running   0\n\nservice/rustfs  ClusterIP  9000/TCP,9001/TCP\nstatefulset.apps/rustfs  1/1"),
    p("Загрузка объекта", "H2RU"),
    code('{\n  "event": "uploaded",\n  "uri": "s3://hh-lake/input/devops_vacancies.ndjson",\n  "bytes": 1628741,\n  "etag": "771f5201731cc0142b40c62aab6056ac"\n}'),
    p("Все последующие Job используют только ClusterIP Service. Это подтверждает, что расчёт не обращается к старому localhost:9000 с хоста и хранилище действительно находится внутри кластера."),
]

story += [
    PageBreak(), p("5. Параллельный расчёт", "H1RU"),
    p("Job pairs-map имеет completionMode: Indexed, completions: 4 и parallelism: 4. Kubernetes передаёт каждому Pod уникальный JOB_COMPLETION_INDEX. Mapper читает объект из RustFS, обрабатывает строки, для которых номер строки по модулю 4 равен индексу, и пишет partials/part-XXXXX.json."),
    code("part 0: selected_rows=1290, unique_pairs=10078, peak=54.96MiB\npart 1: selected_rows=1290, unique_pairs= 9666, peak=54.96MiB\npart 2: selected_rows=1289, unique_pairs=10344, peak=55.20MiB\npart 3: selected_rows=1289, unique_pairs= 8644, peak=54.45MiB"),
    p("Reducer", "H2RU"),
    p("Reducer дождался четырёх объектов, сложил частичные Counter и получил 5 158 строк и 22 286 уникальных пар. Сумма распределения 1290 + 1290 + 1289 + 1289 равна исходным 5 158 строкам: пропусков и двойной обработки нет."),
    code("job.batch/pairs-map condition met: 4/4\njob.batch/pairs-reduce condition met: 1/1\nevent=parallel_reduce_complete rows=5158 unique_pairs=22286\nmapper_peak_rss_mib=[54.96,54.96,55.20,54.45]\nreducer_peak_rss_mib=75.31"),
    p("На reducer пик 75,31MiB выше mapper из-за одновременного хранения четырёх наборов и объединённого Counter, но остаётся ниже limit 128Mi."),
]

top_rows = [["№", "Пара навыков", "ДЗ №3", "Kubernetes"]]
for index, item in enumerate(RESULT["top10"], 1):
    pair = " + ".join(item["skills"])
    top_rows.append([index, pair, item["count"], item["count"]])
story += [
    PageBreak(), p("6. Проверка топ-10", "H1RU"),
    p("Результат reducer сравнивается с сохранённым эталоном artifacts/expected/hw3-top10.json. Сравнение строгое: порядок, написание обоих навыков и целочисленная частота должны совпасть."),
    table(top_rows, [12 * mm, 82 * mm, 34 * mm, 34 * mm]),
    Spacer(1, 6 * mm),
    code("PASS: Kubernetes top-10 exactly matches homework 3 (skills and counts)"),
    p("Совпали все десять позиций. Это одновременно проверяет разбиение файла, отсутствие потерь при S3-чтении, корректность reducer и совместимость алгоритма с ДЗ №3.", "Callout"),
]

story += [
    PageBreak(), p("7. Ожидание при нехватке CPU", "H1RU"),
    p("Deployment cpu-fillers создаёт 40 низкоприоритетных Pod, каждый запрашивает и ограничен 250m CPU. На узле разместились 34 Pod, ещё 6 остались Pending. После насыщения создан cpu-pending с request=limit=2 CPU и тем же низким приоритетом."),
    code("--- CPU saturation before pending pod ---\nPending 6\nRunning 34\n\nNAME          READY   STATUS    NODE\ncpu-pending   0/1     Pending   <none>"),
    code("Warning  FailedScheduling\n0/1 nodes are available: 1 Insufficient cpu.\npreemption: 0/1 nodes are available: 1 No preemption victims found\nfor incoming pod."),
    p("Почему задача не запускается", "H2RU"),
    p("Планировщик суммирует CPU requests уже размещённых Pod. Фактическая загрузка CPU в этот момент не меняет решение: для нового Pod должен помещаться весь request 2 CPU. Вытеснение невозможно, потому что cpu-pending имеет тот же приоритет -100, что и потенциальные жертвы."),
]

story += [
    PageBreak(), p("8. PriorityClass и вытеснение", "H1RU"),
    p("Созданы PriorityClass lab5-low=-100 и lab5-high=1000. После фиксации Pending создан cpu-high с request=2 CPU. Чтобы освободить 2 CPU, kube-scheduler выбрал восемь жертв по 250m и пометил узел как nominated; terminationGracePeriodSeconds=0 сократил задержку."),
    code("Preempted pod/cpu-fillers-...-5wlm5 by high-priority pod\nPreempted pod/cpu-fillers-...-rnzm9 by high-priority pod\nPreempted pod/cpu-fillers-...-7cwq8 by high-priority pod\nPreempted pod/cpu-fillers-...-c64dg by high-priority pod\nPreempted pod/cpu-fillers-...-rmq29 by high-priority pod\nPreempted pod/cpu-fillers-...-7zqrg by high-priority pod\nPreempted pod/cpu-fillers-...-f9j2d by high-priority pod\nPreempted pod/cpu-fillers-...-pz5b4 by high-priority pod"),
    code("NAME       READY   STATUS    NODE\ncpu-high   1/1     Running   lab5-control-plane\nPriority Class Name: lab5-high\nPriority: 1000\nRequests: cpu 2"),
    p("Результат", "Callout"),
    p("Низкоприоритетная задача не могла вытеснить равные ей Pod и ожидала. Высокоприоритетная задача с тем же CPU request получила место после вытеснения восьми Pod. Это отделяет нехватку ресурса от политики приоритетов."),
]

story += [
    PageBreak(), p("9. ResourceQuota", "H1RU"),
    p("В отдельном namespace lab5-quota установлена суммарная квота requests.cpu=500m, requests.memory=256Mi, limits.cpu=1, limits.memory=512Mi и pods=2. Первый Pod запросил 400m CPU; второй запросил ещё 200m."),
    code("pod/quota-first created\n\nError from server (Forbidden): pods \"quota-rejected\" is forbidden:\nexceeded quota: compute-quota, requested: requests.cpu=200m,\nused: requests.cpu=400m, limited: requests.cpu=500m"),
    table([
        ["Ресурс", "Used", "Hard"],
        ["requests.cpu", "400m", "500m"],
        ["requests.memory", "64Mi", "256Mi"],
        ["limits.cpu", "500m", "1"],
        ["limits.memory", "128Mi", "512Mi"],
        ["pods", "1", "2"],
    ], [70 * mm, 46 * mm, 46 * mm]),
    Spacer(1, 6 * mm),
    p("Это admission-ограничение: второй Pod не стал Pending, а вообще не был создан. Квота действует на агрегат namespace и не зависит от наличия свободного CPU на узле."),
]

story += [
    PageBreak(), p("10. Сопоставление Kubernetes, YARN и Mesos", "H1RU"),
    table([
        ["Аспект", "Kubernetes", "YARN", "Mesos"],
        ["Глобальный арбитр", "kube-scheduler", "ResourceManager Scheduler", "Mesos master allocator"],
        ["Агент узла", "kubelet", "NodeManager", "Mesos agent"],
        ["Единица размещения", "Pod", "Container", "Task / executor"],
        ["Логика приложения", "Job controller; при необходимости coordinator/operator", "ApplicationMaster", "Framework scheduler"],
        ["Запуск процесса", "kubelet + container runtime", "NodeManager", "agent запускает executor/task"],
        ["Запрос ресурса", "requests", "Resource capability контейнера", "принятые resource offers"],
        ["Жёсткий предел", "limits / cgroups", "лимит контейнера / cgroups", "containerizer / executor limits"],
        ["Квота", "ResourceQuota на namespace", "CapacityScheduler queues", "quota/limits для roles"],
        ["Приоритет", "PriorityClass + preemption", "priority/queue policy scheduler", "allocation policy/framework logic"],
    ], [31 * mm, 45 * mm, 43 * mm, 43 * mm], "TinyRU"),
    Spacer(1, 5 * mm),
    p("Главное архитектурное различие: YARN централизует переговоры конкретного приложения в ApplicationMaster. Mesos предлагает ресурсы framework scheduler, который сам выбирает предложения. Kubernetes принимает декларативный PodSpec: Job controller создаёт Pod, kube-scheduler выбирает Node, kubelet запускает контейнер."),
]

story += [
    PageBreak(), p("11. Ответы на вопросы", "H1RU"),
    p("Что в Kubernetes соответствует ApplicationMaster YARN?", "H2RU"),
    p("Точного аналога нет. Для обычного batch Job часть обязанностей распределена: Job controller следит за числом успешных Pod, kube-scheduler выбирает узлы, kubelet запускает контейнеры. Если приложению нужны собственные переговоры, зависимости или динамическое создание задач, ближайшим аналогом становится отдельный coordinator Pod или Kubernetes Operator, но он всё равно не выделяет ресурсы напрямую."),
    p("Кто выбирает узел и кто запускает вычисление?", "H2RU"),
    p("В Kubernetes kube-scheduler связывает Pod с Node, затем kubelet через container runtime запускает контейнер. В YARN ResourceManager/Scheduler выделяет контейнер, ApplicationMaster координирует запросы, NodeManager запускает и контролирует контейнер. В Mesos master выдаёт resource offers, framework scheduler принимает предложение и формирует task, а agent запускает executor/task."),
    p("Чем requests отличается от limits?", "H2RU"),
    p("Request участвует в размещении и означает гарантируемую долю для учёта планировщиком. Limit ограничивает уже запущенный контейнер. CPU сверх limit throttled, а память сверх memory limit приводит к реактивному OOM kill. Поэтому Pod может оставаться Pending из-за requests, даже когда фактический CPU визуально простаивает."),
    p("Почему ResourceQuota не равна ёмкости узла?", "H2RU"),
    p("Квота - административный предел namespace и проверяется при admission. Она не обещает наличие ресурса: несколько namespace могут иметь квоты, сумма которых больше ёмкости кластера. Фактическое размещение отдельно выполняет scheduler."),
]

story += [
    PageBreak(), p("12. Ответы на вопросы - продолжение", "H1RU"),
    p("Как обеспечено параллельное разбиение файла?", "H2RU"),
    p("Indexed Job назначил четырём Pod детерминированные индексы. Каждая строка принадлежит ровно одной части по остатку от деления номера строки на 4. Такой способ не требует общей очереди и повторяем. Reducer запускается после состояния Complete 4/4 и суммирует частичные счётчики."),
    p("Как трактовать приоритет и вытеснение?", "H2RU"),
    p("PriorityClass определяет порядок в очереди. Если высокоприоритетный Pod не помещается, scheduler может удалить набор Pod с меньшим числовым приоритетом, достаточный для размещения. Это не то же самое, что node-pressure eviction: здесь инициатором был Pending Pod и дефицит CPU requests."),
    p("Как сопоставить хранение данных?", "H2RU"),
    p("В YARN задачи часто получают локальность относительно блоков HDFS. В Kubernetes S3-объект доступен по Service, но стандартный scheduler не знает о логической локальности объекта; все четыре mapper читают его по сети. В Mesos framework scheduler может использовать атрибуты offers и реализовать собственную политику локальности."),
    p("Почему выбран Indexed Job, а не четыре отдельных Job?", "H2RU"),
    p("Один Indexed Job хранит единое желаемое число завершений, автоматически создаёт индексы и даёт общий статус 4/4. Четыре независимых Job потребовали бы внешней генерации манифестов и отдельного контроля каждого имени."),
]

story += [
    PageBreak(), p("13. Итоги и воспроизведение", "H1RU"),
    p("Локальный кластер Kubernetes v1.34.0 поднят в kind. Образ skill-pairs:lab5 собран и загружен в узел. RustFS работает внутри namespace lab5 и хранит исходный NDJSON размером 1 628 741 байт."),
    p("Зафиксирован OOMKilled с exit code 137 при 64Mi. Рабочий limit 128Mi обоснован измеренным пиком 62,35Mi. Indexed Job из четырёх Pod и reducer вернули 22 286 уникальных пар; top-10 полностью совпал с ДЗ №3."),
    p("Планировщик показал Pending/Insufficient cpu, затем вытеснил восемь Pod с priority -100 для Pod с priority 1000. ResourceQuota отклонила Pod, который увеличивал requests.cpu с 400m до 600m при hard=500m."),
    p("Команды воспроизведения", "H2RU"),
    code("$ make cluster\n$ make image\n$ make storage upload\n$ make baseline oom selected parallel verify\n$ bash scripts/run_experiments.sh"),
    p("Основные артефакты", "H2RU"),
    p("Dockerfile; k8s/00-base.yaml ... 09-quota.yaml; artifacts/logs/00...11; artifacts/results/parallel-top10.json; artifacts/expected/hw3-top10.json; report/build_report.py."),
]

story += [
    PageBreak(), p("14. Использованные источники", "H1RU"),
    p("Kubernetes documentation", "H2RU"),
    p("1. Resource Management for Pods and Containers: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/<br/>2. Jobs: https://kubernetes.io/docs/concepts/workloads/controllers/job/<br/>3. Pod Priority and Preemption: https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/<br/>4. Resource Quotas: https://kubernetes.io/docs/concepts/policy/resource-quotas/<br/>5. Kubernetes Scheduler: https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/"),
    p("YARN", "H2RU"),
    p("6. Apache Hadoop YARN architecture: https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/YARN.html"),
    p("Mesos", "H2RU"),
    p("7. Apache Mesos Architecture: https://mesos.apache.org/documentation/latest/architecture/<br/>8. Apache Mesos Quota: https://mesos.apache.org/documentation/latest/quota/"),
    Spacer(1, 8 * mm),
    p("Все числовые результаты в отчёте взяты из приложенных журналов текущего запуска. Теоретические сопоставления проверены по официальной документации проектов.", "Callout"),
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story)
print(OUTPUT)
