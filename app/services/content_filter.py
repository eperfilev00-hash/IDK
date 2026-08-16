import re
from fastapi import HTTPException, status


# threat patterns
THREAT_PATTERNS = [
    # direct threats
    r'убью', r'прибью', r'затрою', r'задушу', r'зарезать', r'изобью',
    r'заклеваю', r'заклею', r'засужу', r'засажу',
    r'васраню', r'пристрелю', r'застрелю',
    r'накажу', r'отомщу', r'отмщу',
    r'найму', r'закажу', r'скинемся',

    # Threats to / yours
    r'тебе\W*(убью|прибью|затрою|задушу|зарезать)',
    r'тебе\W*(засужу|засажу|накажу|пристрелю)',
    r'твоим\W*(бабе|маме|жене|дочери|брату)',

    # Physical violence
    r'наложу\s+на\s+себя\s+руки',
    r'вдарю', r'хрясну', r'ткну', r'пну',
    r'отправлю\s+на\s+хуй',

    # Threats of violence
    r'припомню', r'вспомню\s+как',
]

# Extortion patterns
EXTORTION_PATTERNS = [
    # Direct extortion
    r'отдавай', r'переводи', r'кинь\s+денег', r'заплати',
    r'заплати\s+мне', r'откуплюсь', r'откуп',

    # Blackmail
    r'расскажу\s+всем', r'опубликую', r'выложу',
    r'покажу\s+родителям', r'покажу\s+начальнику',
    r'залью\s+в\s+сеть', r'залью\s+на\s+reddit',
    r'напишу\s+в\s*([ао]д\w*|деанат|деканат|журнал)',

    # Demand for money/compromising information
    r'дай\s+100', r'дай\s+50', r'дай\s+500', r'дай\s+1000',
    r'скинь\s+на\s+карту', r'скинь\s+на\s+кошелек',
    r'за\s+молчание', r'за\s+то\s+что',

    # Threat of publication
    r'иначе\s+расскажу', r'иначе\s+опубликую',
    r'если\s+не\s+оплатишь', r'если\s+не\s+переведёшь',
    r'если\s+не\s+дашь',
]


def filter_comment_content(content: str) -> str:
    """
    Проверяет контент комментария на запрещённые паттерны.
    
    Разрешены: базовые маты, лайтовые оскорбления.
    Запрещены: угрозы, вымогательство.
    
    Args:
        content: Текст комментария.
        
    Returns:
        Очищенный текст (если заблокирован — raises HTTPException).
        
    Raises:
        HTTPException: Если найден запрещённый паттерн.
    """
    text = content.lower()

    for pattern in THREAT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Комментарий содержит угрозы и не может быть опубликован."
            )

    for pattern in EXTORTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Комментарий содержит признаки вымогательства и не может быть опубликован."
            )

    return content