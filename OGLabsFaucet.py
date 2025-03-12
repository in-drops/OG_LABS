
import random
import time

from loguru import logger
from config import config, Chains
from core.bot import Bot
from core.excel import Excel
from models.account import Account
from utils.inputs import input_pause, input_cycle_pause, input_cycle_amount
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_list_from_file)


def main():
    init_logger()
    if not config.is_browser_run:
        config.is_browser_run = True

    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)
    pause = input_pause()
    cycle_amount = input_cycle_amount()
    cycle_pause = input_cycle_pause()

    for i in range(cycle_amount):
        random.shuffle(accounts_for_work)
        for account in accounts_for_work:
            worker(account)
            random_sleep(pause)

        logger.success(f'Цикл {i + 1} завершен, обработано {len(accounts_for_work)} аккаунтов!')
        logger.info(f'Ожидание перед следующим циклом {cycle_pause} секунд!')
        random_sleep(cycle_pause)

def worker(account: Account) -> None:

    try:
        with Bot(account) as bot:
            activity(bot)
    except Exception as e:
        logger.critical(f"{account.profile_number} Ошибка при инициализации Bot: {e}")

def activity(bot: Bot):

    excel_report = Excel(bot.account, file='OGLabsActivity.xlsx')
    excel_report.set_cell('Address', f'{bot.account.address}')
    excel_report.set_date('Date')

    bot.ads.open_url('https://faucet.0g.ai/')
    random_sleep(5, 10)

    for _ in range(100):
        if bot.ads.page.get_by_role('button', name='Request AOGI Token').is_enabled():
            bot.ads.page.get_by_placeholder('Enter your wallet address').hover()
            bot.ads.page.get_by_placeholder('Enter your wallet address').click()
            random_sleep(3, 5)
            bot.ads.page.get_by_placeholder('Enter your wallet address').fill(bot.account.address)
            random_sleep(3, 5)
            bot.ads.page.get_by_role('button', name='Request AOGI Token').click()
            random_sleep(20,30)
            for _ in range(10):
                if bot.ads.page.get_by_text('Transaction Successful').is_visible():
                    logger.success('Токены $A0GI успешно получены! Данные записаны в таблицу OGLabsActivity.xlsx')
                    excel_report.increase_counter(f'Faucet II A0GI')
                    break
                random_sleep(5, 10)
            else:
                logger.error('Ошибка получения токенов, либо задержка транзакции!')
            break
        random_sleep(3, 5)

    else:
        logger.error('Ошибка получения токенов!')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')


