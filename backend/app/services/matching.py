"""Deterministic, bilingual skill matching; no external services or fuzzy substrings."""
import re
import unicodedata


def tokens(text):
    text = unicodedata.normalize('NFKC', text or '').casefold().replace('ё', 'е')
    return tuple(re.findall(r'[^\W_]+(?:\+\+|#)?', text))


# Explicit phrases rather than stemming: SQL must not match NoSQL, Java != JavaScript.
ALIASES = {
    'Python': ('python', 'питон', 'пайтон'),
    'FastAPI': ('fastapi', 'fast api'),
    'Django': ('django', 'джанго'),
    'SQL': ('sql',),
    'PostgreSQL': ('postgresql', 'postgres', 'постгрес', 'постгресql'),
    'Backend': ('backend', 'back end', 'бэкенд', 'бекенд', 'бэкенд разработчик', 'бэкенд разработка'),
    'Frontend': ('frontend', 'front end', 'фронтенд', 'фронтэнд'),
    'UX/UI': ('ux', 'ui', 'ux ui', 'ui ux', 'дизайн интерфейсов', 'дизайнер интерфейсов', 'интерфейсный дизайн'),
    'Продуктовый дизайн': ('product design', 'product designer', 'продуктовый дизайн', 'продуктовый дизайнер', 'продуктового дизайнера'),
    'Figma': ('figma', 'фигма'),
    'React': ('react', 'reactjs', 'react js', 'реакт'),
    'JavaScript': ('javascript', 'js', 'джаваскрипт'),
    'TypeScript': ('typescript', 'ts', 'тайпскрипт'),
    'Java': ('java', 'джава'),
    'Git': ('git', 'гит'),
    'Docker': ('docker', 'докер'),
    'pytest': ('pytest', 'пай тест'),
    'SQLAlchemy': ('sqlalchemy', 'sql alchemy'),
    'REST API': ('rest api', 'restful api'),
    'Продуктовая аналитика': ('product analytics', 'product analyst', 'продуктовая аналитика', 'продуктовый аналитик', 'продуктового аналитика', 'продуктовые аналитики'),
    'UX-исследования': ('ux research', 'user research', 'ux исследования', 'пользовательские исследования'),
    'FinTech': ('fintech', 'финтех'),
}
PHRASES = {label: tuple(tokens(alias) for alias in aliases) for label, aliases in ALIASES.items()}


def extract_skills(text):
    words = tokens(text)
    return {
        label for label, phrases in PHRASES.items()
        if any(any(words[i:i + len(phrase)] == phrase
                   for i in range(len(words) - len(phrase) + 1))
               for phrase in phrases)
    }


def matched_skills(user_skills, requirements):
    return sorted(user_skills & extract_skills(requirements), key=str.casefold)
