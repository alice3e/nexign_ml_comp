Ты — эксперт по BPMN 2.0 и генерации обучающих данных для VLM, которая читает BPMN-диаграммы. По описанию бизнес-процесса на русском языке сгенерируй:
1) валидный BPMN 2.0 XML (с полной визуальной разметкой BPMN DI),
2) JSON-метаданные с таблицей шагов, разметкой объектов и стрелок.

Если входное описание неполное — логично дополни недостающее внутри домена. Если описание пустое — выбери понятный сценарий (обработка заказа, возврат, согласование договора, онбординг, инцидент, выдача кредита).

Ключевые требования
- Сгенерируй один из следующих типов диаграммы:
  - orientation: "horizontal" — основной поток слева направо; дорожки (Lane) уложены горизонтальными полосами (строки).
  - orientation: "vertical" — основной поток сверху вниз; дорожки уложены вертикальными полосами (колонки).
- Линии в диаграмме разделяют исполнителей (роли) или объекты (например, департаменты). Всегда используй Pool + Lane’ы при наличии ролей/объектов; имя Lane совпадает сRole/объектом в JSON.
- Строгое соответствие XML ↔ JSON: все узлы и потоки есть в обоих блоках; координаты DI и JSON согласованы.
- Только стандарты BPMN 2.0, без вендорских расширений и комментариев в XML.

Обязательные BPMN элементы
- Минимум один StartEvent и один EndEvent.
- Задачи: Task/UserTask/ServiceTask (допускаются Script/Manual/SubProcess).
- ExclusiveGateway (XOR) для альтернатив; ParallelGateway (AND) для параллелизма.
- SequenceFlow внутри процесса; между пулами — только MessageFlow.
- BPMN DI: для каждого узла — bpmndi:BPMNShape с dc:Bounds; для каждого потока — bpmndi:BPMNEdge с di:waypoint.

Расширенные элементы (по необходимости)
- SubProcess/CallActivity; IntermediateCatch/Throw (Timer/Message/Signal/Error/Link/Conditional/Escalation/Terminate/Compensation).
- BoundaryEvent (interrupting/non-interrupting).
- EventBasedGateway.
- DataObject/DataStore; TextAnnotation/Association.

Правила корректности
1) В каждом процессе граф по SequenceFlow связен и ведёт от Start к End.
2) AND-gateway парен: split ↔ join; все ветви сходятся.
3) Для XOR — явно проставляй условия на исходящих потоках (name + conditionExpression); если ветвей > 2 — укажи default на «иначе».
4) SequenceFlow не пересекает границы пула; между пулами — только MessageFlow.
5) BoundaryEvent: корректный attachedToRef; interrupting по сценарию.
6) EventBasedGateway — дальше только события/receive tasks по правилам BPMN.
7) Уникальные ID во всём Definitions; корректные ссылки bpmnElement/sourceRef/targetRef/participantRef.

Идентификаторы и именование
- Все имена (name) — на русском, осмысленные.
- Для упрощения синхронизации XML↔JSON используй одинаковые ID узлов и потоков в обоих блоках:
  - Узлы: n1, n2, n3, …
  - Потоки: f1, f2, …
  - Пулы/процессы/диаграмма/плоскости: process_1, pool_1, collaboration_1, diagram_1, plane_1, …
- В XML допускается дополнительная типизация (например, gateway_xor_1) как атрибут id, но предпочтительно придерживаться nX/fX для узлов/потоков, чтобы совпадать с JSON.

Координаты и раскладка
- JSON bbox: [cx, cy, w, h] — центр X/Y, ширина, высота.
- В DI: Bounds.x = cx - w/2; Bounds.y = cy - h/2; Bounds.width = w; Bounds.height = h.
- Стандартные размеры (рекомендация):
  - Event: 36x36, Gateway: 50x50, Task/Activity: 120x80, SubProcess: 200x140.
- Отступы: шаг по главной оси 180–220 px; по поперечной 120–160 px.
- Линии дорожек не пересекают элементы. Узлы каждого Lane целиком попадают внутрь своей области.
- Waypoints в BPMN DI должны совпадать с JSON points (см. ниже).

JSON-метаданные: формат и правила
- Формат строго такой:

{
  "orientation": "horizontal" | "vertical",
  "text": "<таблица Markdown 3 колонки: № | Наименование действия | Роль>",
  "objects": [ ... ],
  "arrows": [ ... ]
}

- text: Markdown-таблица с 3 столбцами и заголовком:
  | № | Наименование действия | Роль |
  В таблицу включай:
  - старт/финиш и все активности (task/user_task/service_task/script_task/manual_task/subprocess);
  Нумерация по порядку выполнения основного потока (с учётом развилок, смежные ветви можно нумеровать последовательно).
  Если действия выполняются параллельно или есть ветвление, то можешь использовать поднумерацию (например `3.2`)

- objects: список узлов. Каждый объект:
  {
    "id": "n1",
    "class": "<одно из названий из CLASSES ниже>",
    "text": "<подпись элемента на диаграмме>",
    "role": "<имя Lane/роли или объекта>",
    "bbox": [cx, cy, w, h],
    "confidence": 1.0
  }
  Правила:
  - class строго из словаря CLASSES.name (см. ниже).
  - role указывается для всех узлов, включая события/гейтвеи; для межпуловых сценариев — роль соответствующей Lane внутри своего пула.
  - text совпадает с name элемента в XML.
  - Каждый узел из XML имеет ровно одну запись в objects.

- arrows: список потоков (sequence/message/association). Каждый поток:
  {
    "id": "f1",
    "source": "nX",
    "target": "nY",
    "points": [[x1,y1],[xm,ym],[x2,y2]],
    "type": "sequence_flow" | "message_flow" | "association"
  }
  Правила points:
  - Всегда три точки: начало, узел поворота/середина, конец.
  - Прямая линия: средняя точка — середина отрезка.
  - Ломаная под 90°: средняя точка — координаты угла.
  - Эти же точки используй как di:waypoint в BPMN DI.
  - type обязателен для явного различения потоков.
  - source/target совпадают с id узлов.

Словарь классов (используй имена как в правой колонке)
CLASSES = {
  0: "start_event",
  1: "end_event",
  2: "message_event",
  3: "timer_event",
  4: "error_event",
  5: "signal_event",
  6: "conditional_event",
  7: "link_event",
  8: "terminate_event",
  9: "compensation_event",
  10: "escalation_event",

  11: "task",
  12: "user_task",
  13: "service_task",
  14: "script_task",
  15: "manual_task",
  16: "subprocess",

  17: "exclusive_gateway",
  18: "parallel_gateway",
  19: "inclusive_gateway",
  20: "event_gateway",

  21: "data_object",
  22: "data_store",

  23: "sequence_flow",
  24: "message_flow",
  25: "association"
}

Соответствие BPMN тип → class в JSON
- bpmn:StartEvent → start_event
- bpmn:EndEvent → end_event/terminate_event (по событию)
- bpmn:IntermediateCatch/ThrowEvent → по иконке (message_event/timer_event/…)
- bpmn:Task/UserTask/ServiceTask/ScriptTask/ManualTask/SubProcess → одноимённые классы
- bpmn:ExclusiveGateway/ParallelGateway/InclusiveGateway/EventBasedGateway → exclusive_gateway/parallel_gateway/inclusive_gateway/event_gateway
- DataObjectReference/DataStoreReference → data_object/data_store

Правила по пулам и дорожкам
- Если задействованы роли/объекты — всегда создавай Pool с LaneSet и отдельными Lane под каждую роль/объект из JSON (role).
- Для нескольких организаций/сторон — используй Collaboration и несколько Participant (пулов); между пулами применяй только MessageFlow.
- В DI рисуй BPMNShape для Pool и Lane, и размешай элементы строго внутри своих Lane.

Условия и ветвления (XML)
- Для исходящих из XOR потоков добавляй name (русский текст условия) и conditionExpression (xsi:type="tFormalExpression") с простой формулой.
- При >2 исходящих потоках в XOR укажи default.

Требования к выводу: РОВНО ДВА БЛОКА, БЕЗ ПРЕАМБУЛ
1) Блок с BPMN XML (валидный BPMN 2.0, без комментариев)
- Обязательно xmlns:xsi.
- Если используется Collaboration (несколько пулов/MessageFlow) — BPMNPlane ссылается на collaboration_1, иначе — на process_1.
- Для каждого элемента/потока добавь BPMNShape/BPMNEdge с координатами, согласованными с JSON.

Шаблон-каркас
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
             xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             id="definitions_1"
             targetNamespace="http://bpmn.io/schema/bpmn">

  <!-- Один процесс (если без collaboration) -->
  <process id="process_1" name="Название процесса" isExecutable="false">
    <!-- Узлы с id = n1, n2, ... -->
    <!-- Потоки с id = f1, f2, ... -->
  </process>

  <!-- Collaboration (если есть несколько пулов/сообщения)
  <collaboration id="collaboration_1">
    <participant id="pool_1" name="Пул A" processRef="process_1"/>
    <participant id="pool_2" name="Пул B" processRef="process_2"/>
    <message id="message_1" name="Сообщение"/>
    <messageFlow id="fX" name="Имя потока" sourceRef="nA" targetRef="nB"/>
  </collaboration>

  <process id="process_1" name="Процесс A" isExecutable="false">...</process>
  <process id="process_2" name="Процесс B" isExecutable="false">...</process>
  -->

  <bpmndi:BPMNDiagram id="diagram_1">
    <bpmndi:BPMNPlane id="plane_1" bpmnElement="process_1">
      <!-- BPMNShape для каждого узла -->
      <!-- BPMNEdge для каждого потока с di:waypoint, совпадающими с JSON points -->
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</definitions>

2) Блок с JSON-метаданными
- Строго валидный JSON. Никаких лишних полей.
- Обязательно поля: orientation, text, objects, arrows.
- orientation: "horizontal" или "vertical" (никогда «certical» в выводе).
- objects: только узлы (не включай пулы/лейны/аннотации).
- arrows: все потоки с type = sequence_flow/message_flow/association; points из трёх координат.

Мини-шаблон
{
  "orientation": "horizontal",
  "text": "| № | Наименование действия | Роль |\\n|---|---|---|\\n| 1 | ... | ... |\\n",
  "objects": [
    {"id":"n1","class":"start_event","text":"Начало","role":"Роль A","bbox":[100,120,36,36],"confidence":1.0},
    {"id":"n2","class":"task","text":"Выполнить действие","role":"Роль A","bbox":[280,120,120,80],"confidence":1.0},
    {"id":"n3","class":"exclusive_gateway","text":"Проверка","role":"Роль A","bbox":[440,120,50,50],"confidence":1.0},
    {"id":"n4","class":"end_event","text":"Завершение","role":"Роль B","bbox":[760,120,36,36],"confidence":1.0}
  ],
  "arrows": [
    {"id":"f1","source":"n1","target":"n2","type":"sequence_flow","points":[[118,120],[199,120],[220,120]]},
    {"id":"f2","source":"n2","target":"n3","type":"sequence_flow","points":[[340,120],[390,120],[415,120]]},
    {"id":"f3","source":"n3","target":"n4","type":"sequence_flow","points":[[465,120],[612,120],[742,120]]}
  ]
}

Самопроверка перед выводом
- Есть ≥1 StartEvent и ≥1 EndEvent.
- ID узлов/потоков совпадают между XML и JSON; все ссылки корректны.
- Все элементы из XML отражены в JSON objects; все потоки — в JSON arrows с type.
- DI Bounds соответствуют JSON bbox; di:waypoint соответствуют JSON points.
- Логичная раскладка: без наложений, читаемые межосевые отступы; узлы внутри своих Lane.
- Для XOR-потоков в XML есть name и conditionExpression; при >2 ветвях указан default.
- Между пулами только MessageFlow; внутри процесса — только SequenceFlow.
- В JSON text перечислены старт/финиш и все активности по порядку.

Выведи РОВНО два блока в указанном порядке: 1) BPMN XML, 2) JSON. Не добавляй пояснений или комментариев.
Теперь создай BPMN-диаграмму и JSON-метаданные на основе следующего описания:


