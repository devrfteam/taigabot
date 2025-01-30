import logging
import re
import html
from aiohttp import web
from telegram import Bot
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = ''
bot = Bot(token=TELEGRAM_TOKEN)

taiga_users = {
    5: {'username': 'admin', 'full_name': 'Admin', 'telegram_id': 123456789},
}

STATUS_TRANSLATIONS = {
    'New': 'Новая',
    'Ready': 'Готово',
    'In progress': 'В процессе',
    'Ready for test': 'Можно проверять',
    'Closed': 'Завершена',
}

def get_entity_forms(entity_type):
    if entity_type == 'task':
        return {
            'noun': 'задача',
            'adjective': 'новая',  # для согласования с "задача"
            'dative': 'задаче',
            'genitive': 'задачи',
            'prepositional': 'задаче'
        }
    elif entity_type == 'userstory':
        return {
            'noun': 'история',
            'adjective': 'новая',  # для согласования с "история"
            'dative': 'истории',
            'genitive': 'истории',
            'prepositional': 'истории'
        }
    elif entity_type == 'epic':
        return {
            'noun': 'эпик',
            'adjective': 'новый',  # для согласования с "эпик"
            'dative': 'эпику',
            'genitive': 'эпика',
            'prepositional': 'эпике'
        }
    else:
        return {
            'noun': 'объект',
            'adjective': 'новый',
            'dative': 'объекту',
            'genitive': 'объекта',
            'prepositional': 'объекте'
        }

def get_entity_number(link):
    last_part = link.rstrip('/').split('/')[-1]
    return f" #{last_part}" if last_part.isdigit() else ""

def truncate_text(text, limit=150):
    if len(text) > limit:
        return text[:limit] + "..."
    return text

def translate_status(status):
    return STATUS_TRANSLATIONS.get(status, status)

async def send_mention_notification(data_info, telegram_id, comment, entity_type):
    project_name = data_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = data_info.get('subject', 'Без названия')
    link = data_info.get('permalink', '#')
    number = get_entity_number(link)
    entity_forms = get_entity_forms(entity_type)
    truncated_comment = truncate_text(comment)
    message = f"""
👤 <b>Вас упомянули в комментарии к {entity_forms['dative']}{number}!</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_forms['noun'].capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>

<b>Комментарий:</b>
{html.escape(truncated_comment)}
"""
    await bot.send_message(
        chat_id=telegram_id,
        text=message.strip(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    logger.info(f'Уведомление об упоминании отправлено пользователю {telegram_id}')

async def send_comment_notification(data_info, telegram_id, comment, entity_type):
    project_name = data_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = data_info.get('subject', 'Без названия')
    link = data_info.get('permalink', '#')
    number = get_entity_number(link)
    entity_forms = get_entity_forms(entity_type)
    truncated_comment = truncate_text(comment)
    message = f"""
💬 <b>Новый комментарий к {entity_forms['dative']}{number}</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_forms['noun'].capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>

<b>Комментарий:</b>
{html.escape(truncated_comment)}
"""
    await bot.send_message(
        chat_id=telegram_id,
        text=message.strip(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    logger.info(f'Уведомление о комментарии отправлено пользователю {telegram_id}')

async def send_description_change_notification(data_info, telegram_id, entity_type):
    project_name = data_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = data_info.get('subject', 'Без названия')
    link = data_info.get('permalink', '#')
    number = get_entity_number(link)
    entity_forms = get_entity_forms(entity_type)
    message = f"""
📝 <b>Изменено описание в {entity_forms['prepositional']}{number}</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_forms['noun'].capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>
"""
    new_description = data_info.get('description', '')
    if new_description:
        truncated_description = truncate_text(new_description)
        message += f"\n<b>Новое описание:</b>\n{html.escape(truncated_description)}"
    await bot.send_message(
        chat_id=telegram_id,
        text=message.strip(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    logger.info(f'Уведомление об изменении описания отправлено пользователю {telegram_id}')

async def send_status_change_notification(data_info, telegram_id, entity_type, from_status, to_status):
    project_name = data_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = data_info.get('subject', 'Без названия')
    link = data_info.get('permalink', '#')
    number = get_entity_number(link)
    entity_forms = get_entity_forms(entity_type)

    # Перевод статусов на русский
    from_status_rus = translate_status(from_status)
    to_status_rus = translate_status(to_status)

    message = f"""
🔔 <b>Статус {entity_forms['genitive']}{number} изменён</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_forms['noun'].capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>

<b>Статус изменился с</b> <i>{html.escape(from_status_rus)}</i> <b>на</b> <i>{html.escape(to_status_rus)}</i>
"""
    await bot.send_message(
        chat_id=telegram_id,
        text=message.strip(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    logger.info(f'Уведомление об изменении статуса отправлено пользователю {telegram_id}')

async def send_task_assignment(task_info, telegram_id):
    project_name = task_info.get('project', {}).get('name', 'Неизвестный проект')
    task_subject = task_info.get('subject', 'Без названия')
    task_description = task_info.get('description', '')
    task_link = task_info.get('permalink', '#')
    number = get_entity_number(task_link)
    user_story = task_info.get('user_story', {})
    user_story_subject = user_story.get('subject') if user_story else None
    user_story_link = user_story.get('permalink') if user_story else None
    entity_forms = get_entity_forms('task')
    message = f"""
🚀 <b>Вам назначена новая {entity_forms['noun']}{number}</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_forms['noun'].capitalize()}:</b> <a href="{html.escape(task_link, quote=True)}">{html.escape(task_subject)}</a>
"""
    if user_story_subject and user_story_link:
        message += f"\n<b>История:</b> <a href=\"{html.escape(user_story_link, quote=True)}\">{html.escape(user_story_subject)}</a>"
    if task_description:
        truncated_description = truncate_text(task_description)
        message += f"\n<b>Описание задачи:</b>\n{html.escape(truncated_description)}\n"
    await bot.send_message(
        chat_id=telegram_id,
        text=message.strip(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    logger.info(f'Уведомление о назначении задачи отправлено пользователю {telegram_id}')

async def send_userstory_assignment(userstory_info, telegram_id):
    project_name = userstory_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = userstory_info.get('subject', 'Без названия')
    description = userstory_info.get('description', '')
    link = userstory_info.get('permalink', '#')
    number = get_entity_number(link)
    entity_forms = get_entity_forms('userstory')
    message = f"""
🚀 <b>Вам назначена новая {entity_forms['noun']}{number}</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_forms['noun'].capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>
"""
    if description:
        truncated_description = truncate_text(description)
        message += f"\n<b>Описание:</b>\n{html.escape(truncated_description)}\n"
    await bot.send_message(
        chat_id=telegram_id,
        text=message.strip(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    logger.info(f'Уведомление о назначении истории отправлено пользователю {telegram_id}')

async def send_epic_assignment(epic_info, telegram_id):
    project_name = epic_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = epic_info.get('subject', 'Без названия')
    description = epic_info.get('description', '')
    link = epic_info.get('permalink', '#')
    number = get_entity_number(link)
    entity_forms = get_entity_forms('epic')
    message = f"""
🚀 <b>Вам назначен новый {entity_forms['noun']}{number}</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_forms['noun'].capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>
"""
    if description:
        truncated_description = truncate_text(description)
        message += f"\n<b>Описание:</b>\n{html.escape(truncated_description)}\n"
    await bot.send_message(
        chat_id=telegram_id,
        text=message.strip(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    logger.info(f'Уведомление о назначении эпика отправлено пользователю {telegram_id}')

def get_user_ids_from_names(names_list):
    user_ids_set = set()
    for name in names_list:
        for user_id, user_info in taiga_users.items():
            if user_info.get('username') == name or user_info.get('full_name') == name:
                user_ids_set.add(user_id)
    return user_ids_set

async def webhook_handler(request):
    try:
        data = await request.json()
        logger.info('Received webhook: %s', data)
        action = data.get('action')
        entity_type = data.get('type')
        data_info = data.get('data', {})
        change = data.get('change', {})
        diff = change.get('diff', {})

        assigned_user_ids = set()
        if entity_type == 'userstory':
            assigned_users = data_info.get('assigned_users', [])
            assigned_user_ids.update(assigned_users)
        elif entity_type in ('task', 'epic'):
            assigned_to = data_info.get('assigned_to', {})
            if assigned_to and assigned_to.get('id'):
                assigned_user_ids.add(assigned_to.get('id'))

        comment = change.get('comment', '')
        if comment:
            mentioned_usernames = re.findall(r'@(\w+)', comment)
            for mentioned_username in mentioned_usernames:
                for user_id, user_info in taiga_users.items():
                    if user_info.get('username') == mentioned_username:
                        telegram_id = user_info.get('telegram_id')
                        if telegram_id:
                            await send_mention_notification(data_info, telegram_id, comment, entity_type)
                        break

            for user_id in assigned_user_ids:
                user_info = taiga_users.get(user_id)
                if user_info:
                    telegram_id = user_info.get('telegram_id')
                    if telegram_id:
                        await send_comment_notification(data_info, telegram_id, comment, entity_type)

        if 'description_diff' in diff:
            for user_id in assigned_user_ids:
                user_info = taiga_users.get(user_id)
                if user_info:
                    telegram_id = user_info.get('telegram_id')
                    if telegram_id:
                        await send_description_change_notification(data_info, telegram_id, entity_type)

        if 'status' in diff:
            from_status = diff['status'].get('from', 'неизвестно')
            to_status = diff['status'].get('to', 'неизвестно')
            for user_id in assigned_user_ids:
                user_info = taiga_users.get(user_id)
                if user_info:
                    telegram_id = user_info.get('telegram_id')
                    if telegram_id:
                        await send_status_change_notification(data_info, telegram_id, entity_type, from_status, to_status)

        if action in ('create', 'change'):
            if entity_type == 'userstory':
                if 'assigned_users' in diff:
                    from_names = diff['assigned_users'].get('from') or ''
                    to_names = diff['assigned_users'].get('to') or ''

                    from_names_list = [name.strip() for name in from_names.split(',')] if from_names else []
                    to_names_list = [name.strip() for name in to_names.split(',')] if to_names else []

                    from_ids = get_user_ids_from_names(from_names_list)
                    to_ids = get_user_ids_from_names(to_names_list)

                    new_user_ids = to_ids - from_ids

                    for user_id in new_user_ids:
                        user_info = taiga_users.get(user_id)
                        if user_info:
                            telegram_id = user_info.get('telegram_id')
                            if telegram_id:
                                await send_userstory_assignment(data_info, telegram_id)

            elif entity_type in ('task', 'epic'):
                if 'assigned_to' in diff:
                    to_name = diff['assigned_to'].get('to')
                    if to_name:
                        assigned_to_id = None
                        for user_id, user_info in taiga_users.items():
                            if user_info.get('username') == to_name or user_info.get('full_name') == to_name:
                                assigned_to_id = user_id
                                break
                        if assigned_to_id:
                            user_info = taiga_users.get(assigned_to_id)
                            telegram_id = user_info.get('telegram_id')
                            if telegram_id:
                                if entity_type == 'task':
                                    await send_task_assignment(data_info, telegram_id)
                                else:
                                    await send_epic_assignment(data_info, telegram_id)
    except Exception as e:
        logger.exception('Error processing webhook')
    return web.Response(text='OK')

app = web.Application()
app.router.add_post('/webhook', webhook_handler)

if __name__ == '__main__':
    logger.info("Start")
    web.run_app(app, host='0.0.0.0', port=8080)