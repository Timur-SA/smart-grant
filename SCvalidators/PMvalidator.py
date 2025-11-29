import json
from datetime import datetime
from PIL import Image
from pyzbar.pyzbar import decode

def qr2json(qr):
    if qr is None:
        return None
    
    try:
        image = Image.open(qr)
        decoded_objects = decode(image)
        
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode('utf-8')
            return qr_data
        else:
            return None
    except Exception as e:
        return None


# ========================
# Генерация списка переводов по примерам
# ========================

def generate_transfer_list(transfers):
    """
    transfers = [
        # individuals
        {"payer_type": "individual", "inn": "123456789012", "amount": 10000, "date": "2026-01-15"},
        # legal_entities
        {"payer_type": "legal_entity", "inn": "7708123456", "amount": 500000, "mcc": "5047", "date": "2026-02-15"},
        # etc
    ]
    """
    return transfers  # можно просто возвращать, если уже список

# ========================
# Проверка переводов
# ========================

def validate_payments(json_project, transfer_list):
    """
    Сверяет переводы с бюджетом и правилами MCC.
    Возвращает подробный результат проверки по этапам и ошибкам.
    """
    report = []
    errors = []
    stage_lookup = {stage['stage_id']: stage for stage in json_project.get('stages', [])}
    
    # Собираем правильные MCC для каждой allowed_categories вместе с лимитами
    rules_by_stage = {}
    for stage in json_project.get('stages', []):
        stage_id = stage['stage_id']
        rules_by_stage[stage_id] = []
        for rule in stage.get('spending_rules', []):
            norm = {
                "rule_id": rule['rule_id'],
                "rule_type": rule['rule_type'],
                "limit": rule['limit'],
                "allowed_categories": [],
                "allowed_mcc": set(),
            }
            if rule['rule_type'] == 'legal_entities':
                for cat in rule['allowed_categories']:
                    # dict: category + mcc_codes
                    for code in (cat['mcc_codes'] if isinstance(cat,dict) else []):
                        norm["allowed_mcc"].add(str(code))
                    norm["allowed_categories"].append(cat['category'])
            elif rule['rule_type'] == 'individuals':
                norm["allowed_categories"].extend(rule['allowed_categories'])
            rules_by_stage[stage_id].append(norm)
    
    # Сумматоры по правилам
    limits_used = {stage_id: {rule['rule_id']: 0 for rule in stage_rules}
                   for stage_id, stage_rules in rules_by_stage.items()}

    for trn in transfer_list:
        # extract stage (находим по дате)
        stage_id = None
        trn_date = datetime.strptime(trn['date'], "%Y-%m-%d").date()
        for stage in json_project.get('stages', []):
            if stage['start_date'] <= trn['date'] <= stage['end_date']:
                stage_id = stage['stage_id']
        if stage_id is None:
            errors.append(f"❌ Перевод на дату {trn['date']} вне диапазона проекта")
            continue
        rules = rules_by_stage[stage_id]
        matched = False
        
        if trn.get("payer_type") == "individual":
            for rule in rules:
                if rule["rule_type"] == "individuals":
                    limits_used[stage_id][rule['rule_id']] += trn['amount']
                    report.append(
                        f"ФизЛ: ИНН {trn['inn']} сумма {trn['amount']} дата {trn['date']} — В ЭТАПЕ {stage_id} (правило {rule['rule_id']})"
                    )
                    # Проверим лимит
                    if limits_used[stage_id][rule['rule_id']] > rule['limit']:
                        errors.append(
                            f"❌ Превышен лимит для {rule['rule_id']} ({stage_id}): {limits_used[stage_id][rule['rule_id']]} > {rule['limit']}"
                        )
                    matched = True
                    break
            if not matched:
                errors.append(
                    f"❌ Нет подходящего правила для физлица ({trn['inn']}) {trn['date']}"
                )
        elif trn.get("payer_type") == "legal_entity":
            for rule in rules:
                if rule["rule_type"] == "legal_entities" and str(trn["mcc"]) in rule["allowed_mcc"]:
                    limits_used[stage_id][rule['rule_id']] += trn['amount']
                    report.append(
                        f"ЮрЛ: ИНН {trn['inn']} сумма {trn['amount']} мсс {trn['mcc']} дата {trn['date']} — В ЭТАПЕ {stage_id} (правило {rule['rule_id']})"
                    )
                    if limits_used[stage_id][rule['rule_id']] > rule['limit']:
                        errors.append(
                            f"❌ Превышен лимит по MCC для {rule['rule_id']} ({stage_id}): {limits_used[stage_id][rule['rule_id']]} > {rule['limit']}"
                        )
                    matched = True
                    break
            if not matched:
                errors.append(
                    f"❌ Нет разрешения на перевод ЮрЛ ({trn['inn']}, {trn['mcc']}) {trn['date']}"
                )
        else:
            errors.append(f"❌ Не определён тип плательщика: {trn}")
    
    # Итоговый отчет
    return {
        "report": report,
        "errors": errors,
        "limits_used": limits_used,
        "rules_by_stage": rules_by_stage
    }

def handlePayments(grant, report):
    updated_grant = grant
    
    total_spent = sum(sum(rules.values()) for rules in report["limits_used"].values())
    updated_grant['grant_metadata']['total_budget'] -= total_spent


    for stage_id, rules in report["limits_used"].items():       # Обрабатываем каждый этап и правило
        for stage in updated_grant['stages']:                   # Находим соответствующий этап в гранте
            if stage['stage_id'] == stage_id:                   # Обрабатываем каждое правило на этом этапе
                for rule_id, used_amount in rules.items():      # Находим правило и вычитаем использованную сумму из его лимита
                    for rule in stage['spending_rules']:
                        if rule['rule_id'] == rule_id:          # Вычитаем использованную сумму из лимита правила
                            if 'limit' in rule:
                                rule['limit'] -= used_amount
                            rule['spent'] = rule.get('spent', 0) + used_amount
                            break
                break
    
    return updated_grant