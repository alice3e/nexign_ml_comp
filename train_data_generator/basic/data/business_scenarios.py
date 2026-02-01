"""
Бизнес-сценарии для генерации реалистичных BPMN диаграмм.
Содержит доменно-специфичные процессы и терминологию.
"""

# Сценарии для разных бизнес-доменов
BUSINESS_SCENARIOS = {
    "ru": {
        "finance": {
            "name": "Финансы",
            "processes": [
                {
                    "name": "Обработка платежа",
                    "steps": [
                        "Получить платежное поручение",
                        "Проверить реквизиты",
                        "Проверить наличие средств",
                        "Провести транзакцию",
                        "Отправить подтверждение"
                    ],
                    "conditions": ["Средства доступны?", "Реквизиты корректны?", "Лимит превышен?"],
                    "branches": {
                        "yes": ["Одобрено", "Средства есть", "Корректно"],
                        "no": ["Отклонено", "Недостаточно средств", "Ошибка"]
                    }
                },
                {
                    "name": "Выдача кредита",
                    "steps": [
                        "Принять заявку на кредит",
                        "Проверить кредитную историю",
                        "Оценить платежеспособность",
                        "Рассчитать процентную ставку",
                        "Подготовить договор",
                        "Выдать кредит"
                    ],
                    "conditions": ["Кредитная история положительная?", "Доход достаточен?", "Одобрить кредит?"],
                    "branches": {
                        "yes": ["Одобрено", "Достаточно", "Выдать"],
                        "no": ["Отказано", "Недостаточно", "Отклонить"]
                    }
                },
                {
                    "name": "Формирование отчета",
                    "steps": [
                        "Собрать финансовые данные",
                        "Проверить полноту данных",
                        "Рассчитать показатели",
                        "Сформировать отчет",
                        "Согласовать с руководством",
                        "Опубликовать отчет"
                    ],
                    "conditions": ["Данные полные?", "Отчет согласован?", "Требуется корректировка?"],
                    "branches": {
                        "yes": ["Полные", "Согласовано", "Да"],
                        "no": ["Неполные", "Требует доработки", "Нет"]
                    }
                }
            ]
        },
        "logistics": {
            "name": "Логистика",
            "processes": [
                {
                    "name": "Обработка заказа",
                    "steps": [
                        "Получить заказ",
                        "Проверить наличие товара",
                        "Зарезервировать товар",
                        "Упаковать заказ",
                        "Передать в доставку",
                        "Отправить уведомление клиенту"
                    ],
                    "conditions": ["Товар в наличии?", "Адрес доставки корректен?", "Оплата получена?"],
                    "branches": {
                        "yes": ["В наличии", "Корректен", "Оплачено"],
                        "no": ["Нет в наличии", "Некорректен", "Не оплачено"]
                    }
                },
                {
                    "name": "Доставка груза",
                    "steps": [
                        "Принять груз на склад",
                        "Проверить документы",
                        "Сформировать маршрут",
                        "Загрузить транспорт",
                        "Доставить груз",
                        "Получить подпись получателя"
                    ],
                    "conditions": ["Документы в порядке?", "Транспорт доступен?", "Груз доставлен?"],
                    "branches": {
                        "yes": ["В порядке", "Доступен", "Доставлен"],
                        "no": ["Ошибка в документах", "Недоступен", "Не доставлен"]
                    }
                },
                {
                    "name": "Возврат товара",
                    "steps": [
                        "Принять запрос на возврат",
                        "Проверить условия возврата",
                        "Принять товар",
                        "Проверить состояние товара",
                        "Оформить возврат средств",
                        "Вернуть товар на склад"
                    ],
                    "conditions": ["Возврат возможен?", "Товар не поврежден?", "Срок возврата не истек?"],
                    "branches": {
                        "yes": ["Возможен", "Не поврежден", "Не истек"],
                        "no": ["Невозможен", "Поврежден", "Истек"]
                    }
                }
            ]
        },
        "hr": {
            "name": "HR",
            "processes": [
                {
                    "name": "Прием на работу",
                    "steps": [
                        "Получить резюме кандидата",
                        "Провести первичный отбор",
                        "Назначить собеседование",
                        "Провести интервью",
                        "Проверить рекомендации",
                        "Сделать предложение о работе"
                    ],
                    "conditions": ["Кандидат подходит?", "Интервью успешно?", "Рекомендации положительные?"],
                    "branches": {
                        "yes": ["Подходит", "Успешно", "Положительные"],
                        "no": ["Не подходит", "Неуспешно", "Отрицательные"]
                    }
                },
                {
                    "name": "Обработка отпуска",
                    "steps": [
                        "Получить заявление на отпуск",
                        "Проверить доступные дни отпуска",
                        "Согласовать с руководителем",
                        "Проверить график работы",
                        "Утвердить отпуск",
                        "Уведомить сотрудника"
                    ],
                    "conditions": ["Дни отпуска доступны?", "Руководитель согласен?", "График позволяет?"],
                    "branches": {
                        "yes": ["Доступны", "Согласен", "Позволяет"],
                        "no": ["Недоступны", "Не согласен", "Не позволяет"]
                    }
                },
                {
                    "name": "Оценка сотрудника",
                    "steps": [
                        "Запланировать оценку",
                        "Собрать обратную связь",
                        "Провести встречу с сотрудником",
                        "Оценить результаты работы",
                        "Составить план развития",
                        "Утвердить оценку"
                    ],
                    "conditions": ["Результаты удовлетворительные?", "Требуется обучение?", "Повышение возможно?"],
                    "branches": {
                        "yes": ["Удовлетворительные", "Требуется", "Возможно"],
                        "no": ["Неудовлетворительные", "Не требуется", "Невозможно"]
                    }
                }
            ]
        },
        "it": {
            "name": "IT",
            "processes": [
                {
                    "name": "Обработка инцидента",
                    "steps": [
                        "Зарегистрировать инцидент",
                        "Классифицировать проблему",
                        "Назначить ответственного",
                        "Диагностировать причину",
                        "Устранить проблему",
                        "Закрыть инцидент"
                    ],
                    "conditions": ["Проблема критична?", "Требуется эскалация?", "Проблема решена?"],
                    "branches": {
                        "yes": ["Критична", "Требуется", "Решена"],
                        "no": ["Некритична", "Не требуется", "Не решена"]
                    }
                },
                {
                    "name": "Развертывание обновления",
                    "steps": [
                        "Подготовить обновление",
                        "Протестировать на тестовой среде",
                        "Создать резервную копию",
                        "Развернуть на продакшене",
                        "Проверить работоспособность",
                        "Уведомить пользователей"
                    ],
                    "conditions": ["Тесты пройдены?", "Резервная копия создана?", "Обновление успешно?"],
                    "branches": {
                        "yes": ["Пройдены", "Создана", "Успешно"],
                        "no": ["Не пройдены", "Не создана", "Ошибка"]
                    }
                },
                {
                    "name": "Предоставление доступа",
                    "steps": [
                        "Получить запрос на доступ",
                        "Проверить полномочия запрашивающего",
                        "Согласовать с владельцем ресурса",
                        "Создать учетную запись",
                        "Настроить права доступа",
                        "Уведомить пользователя"
                    ],
                    "conditions": ["Запрос одобрен?", "Пользователь авторизован?", "Доступ настроен?"],
                    "branches": {
                        "yes": ["Одобрен", "Авторизован", "Настроен"],
                        "no": ["Отклонен", "Не авторизован", "Ошибка настройки"]
                    }
                }
            ]
        }
    },
    "en": {
        "finance": {
            "name": "Finance",
            "processes": [
                {
                    "name": "Payment Processing",
                    "steps": [
                        "Receive payment order",
                        "Verify account details",
                        "Check fund availability",
                        "Process transaction",
                        "Send confirmation"
                    ],
                    "conditions": ["Funds available?", "Details correct?", "Limit exceeded?"],
                    "branches": {
                        "yes": ["Approved", "Funds available", "Correct"],
                        "no": ["Rejected", "Insufficient funds", "Error"]
                    }
                },
                {
                    "name": "Loan Approval",
                    "steps": [
                        "Receive loan application",
                        "Check credit history",
                        "Assess creditworthiness",
                        "Calculate interest rate",
                        "Prepare contract",
                        "Disburse loan"
                    ],
                    "conditions": ["Credit history positive?", "Income sufficient?", "Approve loan?"],
                    "branches": {
                        "yes": ["Approved", "Sufficient", "Grant"],
                        "no": ["Rejected", "Insufficient", "Deny"]
                    }
                },
                {
                    "name": "Report Generation",
                    "steps": [
                        "Collect financial data",
                        "Verify data completeness",
                        "Calculate metrics",
                        "Generate report",
                        "Get management approval",
                        "Publish report"
                    ],
                    "conditions": ["Data complete?", "Report approved?", "Correction needed?"],
                    "branches": {
                        "yes": ["Complete", "Approved", "Yes"],
                        "no": ["Incomplete", "Needs revision", "No"]
                    }
                }
            ]
        },
        "logistics": {
            "name": "Logistics",
            "processes": [
                {
                    "name": "Order Processing",
                    "steps": [
                        "Receive order",
                        "Check product availability",
                        "Reserve product",
                        "Pack order",
                        "Hand over to delivery",
                        "Send customer notification"
                    ],
                    "conditions": ["Product available?", "Delivery address correct?", "Payment received?"],
                    "branches": {
                        "yes": ["Available", "Correct", "Paid"],
                        "no": ["Out of stock", "Incorrect", "Not paid"]
                    }
                },
                {
                    "name": "Cargo Delivery",
                    "steps": [
                        "Accept cargo at warehouse",
                        "Verify documents",
                        "Plan route",
                        "Load transport",
                        "Deliver cargo",
                        "Get recipient signature"
                    ],
                    "conditions": ["Documents valid?", "Transport available?", "Cargo delivered?"],
                    "branches": {
                        "yes": ["Valid", "Available", "Delivered"],
                        "no": ["Document error", "Unavailable", "Not delivered"]
                    }
                },
                {
                    "name": "Product Return",
                    "steps": [
                        "Receive return request",
                        "Check return conditions",
                        "Accept product",
                        "Inspect product condition",
                        "Process refund",
                        "Return product to warehouse"
                    ],
                    "conditions": ["Return allowed?", "Product undamaged?", "Return period valid?"],
                    "branches": {
                        "yes": ["Allowed", "Undamaged", "Valid"],
                        "no": ["Not allowed", "Damaged", "Expired"]
                    }
                }
            ]
        },
        "hr": {
            "name": "HR",
            "processes": [
                {
                    "name": "Employee Hiring",
                    "steps": [
                        "Receive candidate resume",
                        "Conduct initial screening",
                        "Schedule interview",
                        "Conduct interview",
                        "Check references",
                        "Make job offer"
                    ],
                    "conditions": ["Candidate suitable?", "Interview successful?", "References positive?"],
                    "branches": {
                        "yes": ["Suitable", "Successful", "Positive"],
                        "no": ["Not suitable", "Unsuccessful", "Negative"]
                    }
                },
                {
                    "name": "Leave Processing",
                    "steps": [
                        "Receive leave request",
                        "Check available leave days",
                        "Get manager approval",
                        "Check work schedule",
                        "Approve leave",
                        "Notify employee"
                    ],
                    "conditions": ["Leave days available?", "Manager approved?", "Schedule allows?"],
                    "branches": {
                        "yes": ["Available", "Approved", "Allows"],
                        "no": ["Unavailable", "Not approved", "Doesn't allow"]
                    }
                },
                {
                    "name": "Employee Evaluation",
                    "steps": [
                        "Schedule evaluation",
                        "Collect feedback",
                        "Meet with employee",
                        "Assess performance",
                        "Create development plan",
                        "Approve evaluation"
                    ],
                    "conditions": ["Performance satisfactory?", "Training needed?", "Promotion possible?"],
                    "branches": {
                        "yes": ["Satisfactory", "Needed", "Possible"],
                        "no": ["Unsatisfactory", "Not needed", "Not possible"]
                    }
                }
            ]
        },
        "it": {
            "name": "IT",
            "processes": [
                {
                    "name": "Incident Handling",
                    "steps": [
                        "Register incident",
                        "Classify problem",
                        "Assign responsible person",
                        "Diagnose cause",
                        "Resolve problem",
                        "Close incident"
                    ],
                    "conditions": ["Problem critical?", "Escalation needed?", "Problem resolved?"],
                    "branches": {
                        "yes": ["Critical", "Needed", "Resolved"],
                        "no": ["Not critical", "Not needed", "Not resolved"]
                    }
                },
                {
                    "name": "Update Deployment",
                    "steps": [
                        "Prepare update",
                        "Test on staging environment",
                        "Create backup",
                        "Deploy to production",
                        "Verify functionality",
                        "Notify users"
                    ],
                    "conditions": ["Tests passed?", "Backup created?", "Update successful?"],
                    "branches": {
                        "yes": ["Passed", "Created", "Successful"],
                        "no": ["Failed", "Not created", "Error"]
                    }
                },
                {
                    "name": "Access Provisioning",
                    "steps": [
                        "Receive access request",
                        "Verify requester authority",
                        "Get resource owner approval",
                        "Create user account",
                        "Configure access rights",
                        "Notify user"
                    ],
                    "conditions": ["Request approved?", "User authorized?", "Access configured?"],
                    "branches": {
                        "yes": ["Approved", "Authorized", "Configured"],
                        "no": ["Rejected", "Not authorized", "Configuration error"]
                    }
                }
            ]
        }
    }
}