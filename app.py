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

# Словарь с информацией о пользователях Taiga и их Telegram ID
taiga_users = {
    5: {'username': 'user1', 'full_name': 'Иван Иванов', 'telegram_id': 12345678},
    6: {'username': 'user2', 'full_name': 'Петр Петров', 'telegram_id': 12345678},
}

def get_entity_label(entity_type):
    if entity_type == 'task':
        return 'задаче'
    elif entity_type == 'userstory':
        return 'пользовательской истории'
    elif entity_type == 'epic':
        return 'эпике'
    else:
        return 'объекте'

async def send_mention_notification(data_info, telegram_id, comment, entity_type):
    project_name = data_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = data_info.get('subject', 'Без названия')
    link = data_info.get('permalink', '#')
    entity_label = get_entity_label(entity_type)
    message = f"""
👤 <b>Вас упомянули в комментарии к {entity_label}!</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_label.capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>

<b>Комментарий:</b>
{html.escape(comment)}
"""
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message.strip(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f'Уведомление об упоминании отправлено пользователю {telegram_id}')
    except Exception as e:
        logger.exception(f'Не удалось отправить уведомление пользователю {telegram_id}')

async def send_comment_notification(data_info, telegram_id, comment, entity_type):
    project_name = data_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = data_info.get('subject', 'Без названия')
    link = data_info.get('permalink', '#')
    entity_label = get_entity_label(entity_type)
    message = f"""
💬 <b>Новый комментарий к {entity_label}!</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_label.capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>

<b>Комментарий:</b>
{html.escape(comment)}
"""
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message.strip(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f'Уведомление о комментарии отправлено пользователю {telegram_id}')
    except Exception as e:
        logger.exception(f'Не удалось отправить уведомление пользователю {telegram_id}')

async def send_description_change_notification(data_info, telegram_id, entity_type):
    project_name = data_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = data_info.get('subject', 'Без названия')
    link = data_info.get('permalink', '#')
    entity_label = get_entity_label(entity_type)
    message = f"""
📝 <b>Изменено описание в {entity_label}!</b>

<b>Проект:</b> {html.escape(project_name)}
<b>{entity_label.capitalize()}:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>
"""
    new_description = data_info.get('description', '')
    if new_description:
        message += f"\n<b>Новое описание:</b>\n{html.escape(new_description)}"
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message.strip(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f'Уведомление об изменении описания отправлено пользователю {telegram_id}')
    except Exception as e:
        logger.exception(f'Не удалось отправить уведомление пользователю {telegram_id}')

async def send_task_assignment(task_info, telegram_id):
    project_name = task_info.get('project', {}).get('name', 'Неизвестный проект')
    task_subject = task_info.get('subject', 'Без названия')
    task_description = task_info.get('description', '')
    task_link = task_info.get('permalink', '#')
    user_story = task_info.get('user_story', {})
    user_story_subject = user_story.get('subject') if user_story else None
    user_story_link = user_story.get('permalink') if user_story else None
    entity_label = 'задача'
    message = f"""
🚀 <b>Вам назначена новая {entity_label}!</b>

<b>Проект:</b> {html.escape(project_name)}
<b>Задача:</b> <a href="{html.escape(task_link, quote=True)}">{html.escape(task_subject)}</a>
"""
    if user_story_subject and user_story_link:
        message += f"<b>Пользовательская история:</b> <a href=\"{html.escape(user_story_link, quote=True)}\">{html.escape(user_story_subject)}</a>\n"
    if task_description:
        message += f"\n<b>Описание задачи:</b>\n{html.escape(task_description)}\n"
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message.strip(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f'Уведомление о назначении задачи отправлено пользователю {telegram_id}')
    except Exception as e:
        logger.exception(f'Не удалось отправить сообщение пользователю {telegram_id}')

async def send_userstory_assignment(userstory_info, telegram_id):
    project_name = userstory_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = userstory_info.get('subject', 'Без названия')
    description = userstory_info.get('description', '')
    link = userstory_info.get('permalink', '#')
    entity_label = 'пользовательская история'
    message = f"""
🚀 <b>Вам назначена новая {entity_label}!</b>

<b>Проект:</b> {html.escape(project_name)}
<b>Пользовательская история:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>
"""
    if description:
        message += f"\n<b>Описание:</b>\n{html.escape(description)}\n"
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message.strip(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f'Уведомление о назначении пользовательской истории отправлено пользователю {telegram_id}')
    except Exception as e:
        logger.exception(f'Не удалось отправить сообщение пользователю {telegram_id}')

async def send_epic_assignment(epic_info, telegram_id):
    project_name = epic_info.get('project', {}).get('name', 'Неизвестный проект')
    subject = epic_info.get('subject', 'Без названия')
    description = epic_info.get('description', '')
    link = epic_info.get('permalink', '#')
    entity_label = 'эпик'
    message = f"""
🚀 <b>Вам назначен новый {entity_label}!</b>

<b>Проект:</b> {html.escape(project_name)}
<b>Эпик:</b> <a href="{html.escape(link, quote=True)}">{html.escape(subject)}</a>
"""
    if description:
        message += f"\n<b>Описание:</b>\n{html.escape(description)}\n"
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message.strip(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f'Уведомление о назначении эпика отправлено пользователю {telegram_id}')
    except Exception as e:
        logger.exception(f'Не удалось отправить сообщение пользователю {telegram_id}')

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

        # Формируем список назначенных пользователей
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
            # Упоминания в комментариях
            mentioned_usernames = re.findall(r'@(\w+)', comment)
            for mentioned_username in mentioned_usernames:
                for user_id, user_info in taiga_users.items():
                    if user_info.get('username') == mentioned_username:
                        telegram_id = user_info.get('telegram_id')
                        if telegram_id:
                            await send_mention_notification(data_info, telegram_id, comment, entity_type)
                        else:
                            logger.warning(f'No Telegram ID found for Taiga user ID {user_id}')
                        break
                else:
                    logger.warning(f'No Taiga user ID found for username {mentioned_username}')

            # Уведомления назначенным пользователям
            for user_id in assigned_user_ids:
                user_info = taiga_users.get(user_id)
                if user_info:
                    telegram_id = user_info.get('telegram_id')
                    if telegram_id:
                        await send_comment_notification(data_info, telegram_id, comment, entity_type)
                    else:
                        logger.warning(f'No Telegram ID found for Taiga user ID {user_id}')
                else:
                    logger.warning(f'No user info found for Taiga user ID {user_id}')

        if 'description_diff' in diff:
            # Уведомления об изменении описания
            for user_id in assigned_user_ids:
                user_info = taiga_users.get(user_id)
                if user_info:
                    telegram_id = user_info.get('telegram_id')
                    if telegram_id:
                        await send_description_change_notification(data_info, telegram_id, entity_type)
                    else:
                        logger.warning(f'No Telegram ID found for Taiga user ID {user_id}')
                else:
                    logger.warning(f'No user info found for Taiga user ID {user_id}')

        # Обработка назначений при изменении ответственного
        if action in ('create', 'change'):
            if entity_type == 'userstory':
                if 'assigned_users' in diff:
                    # Изменились назначенные пользователи
                    from_names = diff['assigned_users'].get('from') or ''
                    to_names = diff['assigned_users'].get('to') or ''

                    from_names_list = [name.strip() for name in from_names.split(',')] if from_names else []
                    to_names_list = [name.strip() for name in to_names.split(',')] if to_names else []

                    from_ids = get_user_ids_from_names(from_names_list)
                    to_ids = get_user_ids_from_names(to_names_list)

                    # Получаем список новых назначенных пользователей
                    new_user_ids = to_ids - from_ids

                    for user_id in new_user_ids:
                        user_info = taiga_users.get(user_id)
                        if user_info:
                            telegram_id = user_info.get('telegram_id')
                            if telegram_id:
                                await send_userstory_assignment(data_info, telegram_id)
                            else:
                                logger.warning(f'No Telegram ID found for Taiga user ID {user_id}')
                        else:
                            logger.warning(f'No user info found for Taiga user ID {user_id}')

            elif entity_type in ('task', 'epic'):
                if 'assigned_to' in diff:
                    to_name = diff['assigned_to'].get('to')
                    if to_name:
                        # Ищем ID пользователя по имени пользователя или полному имени
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
                            else:
                                logger.warning(f'No Telegram ID found for Taiga user ID {assigned_to_id}')
                        else:
                            logger.warning(f'No Taiga user ID found for username or full name {to_name}')
                    else:
                        logger.warning('No assigned_to information in diff')
            else:
                logger.info('Webhook не содержит релевантных изменений для назначений.')

    except Exception as e:
        logger.exception('Error processing webhook')
    return web.Response(text='OK')

app = web.Application()
app.router.add_post('/webhook', webhook_handler)

if __name__ == '__main__':
    logger.info("Start")
    web.run_app(app, host='0.0.0.0', port=8080)