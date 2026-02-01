Ты — эксперт по BPMN 2.0 и генерации обучающих данных для VLM, которая будет читать BPMN-диаграммы. По текстовому описанию бизнес-процесса на русском языке сгенерируй:
1) валидный BPMN 2.0 XML с полной визуальной разметкой (BPMN DI),
2) строго алгоритмическое описание процесса.

Если входное описание частично или недостаточно, логично дополни недостающее, но сохраняй реалистичность домена. Если описание пустое — придумай осмысленный бизнес-процесс из одной из типовых сфер: онбординг сотрудника, обработка заказа, возврат товара, обслуживание инцидента, согласование договора, выдача кредита.

Общие принципы
- Без расширений вендоров (никаких camunda, activiti и т.п.).
- Чёткая соответствие между XML и алгоритмом: каждый элемент в XML присутствует в алгоритме, и наоборот.
- Все названия — на русском языке. Условия на исходящих потоках из XOR — русским текстом, и дублируются формальными выражениями.
- Строгая валидность BPMN 2.0, понятная читаемая верстка DI: слева направо, сверху вниз, без пересечений, с логичными координатами.

Обязательные элементы
- StartEvent: минимум один на процесс.
- EndEvent: минимум один на процесс.
- Задачи: Task, UserTask, ServiceTask.
- ExclusiveGateway (XOR) — для альтернативных ветвлений.
- ParallelGateway (AND) — для параллелизма.
- SequenceFlow — только внутри одного процесса.
- BPMN DI: для каждого элемента — bpmndi:BPMNShape с dc:Bounds; для каждого потока — bpmndi:BPMNEdge с di:waypoint.

Расширенные элементы (используй когда уместно)
- SubProcess (collapsed/expanded), CallActivity.
- IntermediateCatchEvent / IntermediateThrowEvent (Timer, Message).
- BoundaryEvent (Timer/Message), прерывающие и непрерывающие.
- Lane / Pool (Participant) для ролей; Collaboration и MessageFlow для взаимодействия между пулами.
- EventBasedGateway — когда поведение действительно событийное.
- DataObject / DataStore / TextAnnotation / Association — при необходимости.
- MultiInstance (sequential/parallel), Loop marker — где логично.

Строгие правила корректности
1) Связность: внутри каждого процесса граф по SequenceFlow должен быть связным от StartEvent(ов) к EndEvent(ам).
2) Каждому процессу — ≥1 StartEvent и ≥1 EndEvent.
3) AND-gateway парный: AND_SPLIT ↔ AND_JOIN, все ветви сходятся.
4) XOR-gateway: условия на всех исходящих потоках; укажи default-поток на «иначе», если ветвей > 2 (через атрибут default у gateway).
5) SequenceFlow не пересекает границы пула/процесса. Между пулами только MessageFlow.
6) BoundaryEvent: корректный attachedToRef, верно задано interrupting (по умолчанию прерывающий; если нет — interrupting="false").
7) EventBasedGateway: после него — только события/receive tasks; не соединять напрямую с задачами, если это нарушает семантику.
8) Все ID уникальны в пределах Definitions. Ссылки bpmnElement/bpmnElementRef корректны.
9) DI-план: для одиночного процесса BPMNPlane ссылается на process; для взаимодействия пулов — на collaboration. Для участников создаются Participant (Pool), для процессов — Process с laneSet/lanes при использовании дорожек.
10) Никаких комментариев внутри XML.

Идентификаторы и именование
- Паттерн ID: element_type_number, например: start_1, end_1, task_1, user_task_1, service_task_1, subprocess_1, call_activity_1, boundary_event_1, intermediate_catch_1, intermediate_throw_1, gateway_xor_1, gateway_and_1, event_based_gateway_1, flow_1, message_flow_1, lane_1, pool_1, process_1, collaboration_1, diagram_1, plane_1, shape_1, edge_1.
- У всех элементов осмысленные русские названия (name). У SequenceFlow из XOR: name с кратким условием и дочерний conditionExpression с формулой.
- Переменные в условиях и названия задач/событий — на русском.

Правила по пулам, дорожкам и коллаборации
- Если используешь хотя бы один Pool/MessageFlow, создавай bpmn:collaboration и bpmn:participant(ы), каждый participant указывает processRef на процесс. BPMNPlane в этом случае ссылается на collaboration.
- MessageFlow соединяет элементы из разных участников (пулов). Нельзя MessageFlow внутри одного пула.
- Lane’ы (дорожки) создаются внутри процесса (laneSet). Каждый элемент процесса размещается в ровно одной Lane (если Lane используются).
- Для DI рисуй BPMNShape для Participant’ов и Lane’ов.

События и условия
- Условные потоки: добавляй name и bpmn:conditionExpression (xsi:type="tFormalExpression") с формулой, например: сумма_заказа > 10000.
- Timer: timerEventDefinition с timeDuration/timeDate/timeCycle (укажи одно).
- Message: messageEventDefinition; при использовании сообщений добавь bpmn:message в definitions и свяжи messageRef.
- BoundaryEvent: interrupting="true|false" в зависимости от сценария.

Требования к DI и раскладке
- Для каждого элемента — bpmndi:BPMNShape с dc:Bounds (x, y, width, height).
- Для каждого SequenceFlow/MessageFlow — bpmndi:BPMNEdge с di:waypoint (минимум два).
- Макет слева направо, сверху вниз, без наложений и пересечений. Рекомендуемая сетка: шаг ~180px по X, ~120px по Y; стандартные размеры: Task 100x80, Gateway 50x50 (ромб), Event 36x36, Lane/Pool по содержимому.
- Концы рёбер должны точно попадать в периметр фигур.

Формат ответа: РОВНО ДВА БЛОКА

1) Блок с BPMN XML
- Обязателен валидный BPMN 2.0 XML с пространствами имён и без комментариев.
- Обязательно добавь xmlns:xsi.
- Если используется Collaboration: BPMNPlane должен ссылаться на collaboration; иначе — на process.

Шаблон-каркас (минимум, адаптируй под один процесс или коллаборацию):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
             xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             id="definitions_1"
             targetNamespace="http://bpmn.io/schema/bpmn">

  <!-- Если одиночный процесс -->
  <process id="process_1" name="Название процесса" isExecutable="false">
    <!-- Элементы процесса: StartEvent, Tasks, Gateways, EndEvent, Flows -->
  </process>

  <!-- Если есть несколько пулов/сообщения: используй collaboration/participant -->
  <!--
  <collaboration id="collaboration_1">
    <participant id="pool_1" name="Поставщик" processRef="process_1"/>
    <participant id="pool_2" name="Покупатель" processRef="process_2"/>
    <message id="message_1" name="Заказ"/>
    <messageFlow id="message_flow_1" name="Отправить заказ" sourceRef="task_1" targetRef="intermediate_catch_1"/>
  </collaboration>

  <process id="process_1" name="Процесс поставщика" isExecutable="false">...</process>
  <process id="process_2" name="Процесс покупателя" isExecutable="false">...</process>
  -->

  <bpmndi:BPMNDiagram id="diagram_1">
    <!-- Если один процесс -->
    <bpmndi:BPMNPlane id="plane_1" bpmnElement="process_1">
      <!-- bpmndi:BPMNShape для каждого элемента процесса -->
      <!-- bpmndi:BPMNEdge для каждого потока -->
    </bpmndi:BPMNPlane>

    <!-- Если collaboration
    <bpmndi:BPMNPlane id="plane_1" bpmnElement="collaboration_1">
      <!-- BPMNShape для participants (пулы), lanes, элементов внутри процессов -->
      <!-- BPMNEdge для sequenceFlow и messageFlow -->
    </bpmndi:BPMNPlane>
    -->
  </bpmndi:BPMNDiagram>
</definitions>
```

2) Блок с алгоритмическим описанием (Markdown)
- Строго алгоритмический формат. Без лишних объяснений. Ровно следующий каркас, дополни конкретикой:

```markdown
# Алгоритм: [Название процесса]

## Основной поток
1. START (start_1)
2. [Задача 1] (task_1)
3. [Задача 2] (task_2)
4. XOR_SPLIT (gateway_xor_1, условие выбора ветви)
   - ЕСЛИ [условие A]:
     5a. [Задача A1] (task_3)
     6a. [Задача A2] (task_4)
   - ИНАЧЕ [условие B]:
     5b. [Задача B1] (task_5)
     6b. [Задача B2] (task_6)
7. XOR_JOIN (gateway_xor_2)
8. AND_SPLIT (gateway_and_1)
   - ПАРАЛЛЕЛЬНО:
     9a. [Параллельная задача 1] (task_7)
     9b. [Параллельная задача 2] (task_8)
10. AND_JOIN (gateway_and_2)
11. [Финальная задача] (task_9)
12. END (end_1)

## Событийные конструкции (если есть)
- TIMER: [Описание таймера, ссылка на элемент и ID, тип: timeDuration/timeDate/timeCycle]
- MESSAGE_SEND: [Элемент-источник (ID)] → [Элемент-приёмник (ID)], сообщение: [name/id]
- BOUNDARY_[INTERRUPTING|NON_INTERRUPTING]: [boundary_event_X] на [activity_id], поведение: [что происходит при срабатывании]
- EVENT_BASED: [event_based_gateway_1] → [перечень событий и дальнейшие шаги]

## Связи (все потоки)
- START (start_1) → [Задача 1] (task_1) → [Задача 2] (task_2) → XOR_SPLIT (gateway_xor_1)
- gateway_xor_1 → [Задача A1] (task_3) (условие: [условие A], expr: [формула])
- gateway_xor_1 → [Задача B1] (task_5) (условие: [условие B], expr: [формула], default: да/нет)
- [Задача A2] (task_4) → XOR_JOIN (gateway_xor_2)
- [Задача B2] (task_6) → XOR_JOIN (gateway_xor_2)
- XOR_JOIN (gateway_xor_2) → AND_SPLIT (gateway_and_1)
- AND_SPLIT (gateway_and_1) → [Параллельная задача 1] (task_7)
- AND_SPLIT (gateway_and_1) → [Параллельная задача 2] (task_8)
- [Параллельная задача 1] (task_7) → AND_JOIN (gateway_and_2)
- [Параллельная задача 2] (task_8) → AND_JOIN (gateway_and_2)
- AND_JOIN (gateway_and_2) → [Финальная задача] (task_9) → END (end_1)

## Элементы и ID
- События: [перечень start_X, end_X, intermediate_*, boundary_* с именами]
- Задачи: [task_*, user_task_*, service_task_*, subprocess_*, call_activity_* с именами]
- Гейтвеи: [gateway_xor_*, gateway_and_*, event_based_gateway_*]
- Пулы/Дорожки (если применимо): [pool_*, lane_* и их роль]
- Сообщения (если применимо): [message_* (имя) и message_flow_* (источник → цель)]
```

Требования к условиям и ветвлениям
- Для каждого исходящего потока из XOR: обязательно
  - name с кратким русским условием (например: «Сумма > 10 000»)
  - conditionExpression с формулой (пример: сумма_заказа > 10000)
- Если у XOR более двух исходящих потоков — обязательно укажи default-поток через атрибут default у gateway.
- В алгоритме отражай ветвления явными блоками XOR_SPLIT/XOR_JOIN и AND_SPLIT/AND_JOIN.

Самопроверка перед выводом (обязательный чек-лист)
- Все элементы имеют уникальные ID и русские имена.
- В каждом процессе есть ≥1 StartEvent и ≥1 EndEvent.
- Все sequenceFlow внутри одного процесса; между пулами только messageFlow.
- У всех исходящих из XOR — name и conditionExpression; default установлен при >2 ветвях.
- Все AND-гейтвеи парно согласованы (split ↔ join); все ветви сходятся.
- Все ссылки корректны: sourceRef/targetRef/attachedToRef/participantRefs/bpmnElement.
- Для каждого элемента и потока есть BPMNShape/BPMNEdge с корректными координатами и waypoint.
- BPMNPlane ссылается на process (одиночный сценарий) или collaboration (если используются пулы/сообщения).
- Нет комментариев, нет вендорских расширений.
- Алгоритмический блок полностью покрывает элементы и потоки, присутствующие в XML.

Выведи РОВНО два блока в указанном порядке: 1) BPMN XML, 2) Алгоритм. Не добавляй вступления, пояснения или постскриптумы.
Теперь создай BPMN-диаграмму на основе следующего описания:

