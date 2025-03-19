
import random
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
    bot.metamask.auth_metamask()
    bot.metamask.select_chain(Chains.OGLABS_TESTNET)
    bot.ads.open_url('https://test.zer0.exchange/swap')
    random_sleep(10, 20)
    connect_button = bot.ads.page.get_by_role('button', name='Connect')
    if connect_button.count():
        bot.ads.page.get_by_role('button', name='Connect').nth(0).click()
        random_sleep(2, 3)
        bot.ads.page.get_by_text('MetaMask').click()
        bot.metamask.universal_confirm()
        random_sleep(5, 10)


    '''SWAPS'''
    USDT_token = bot.ads.page.locator("p.mantine-focus-auto.m_b6d8b162.zer0dex-Text-root").filter(has_text="TETHER USD")
    ETH_token = bot.ads.page.locator("p.mantine-focus-auto.m_b6d8b162.zer0dex-Text-root").filter(has_text="ETHEREUM")
    BTC_token = bot.ads.page.locator("p.mantine-focus-auto.m_b6d8b162.zer0dex-Text-root").filter(has_text="BITCOIN")

    tokens_out = [USDT_token, ETH_token, BTC_token]
    # tokens_in = [USDT_token, ETH_token, BTC_token]
    swaps = 0
    random_count = random.randint(5, 10)
    no_balance_tokens = 0

    while swaps < random_count:
        for token_out in tokens_out:
            if no_balance_tokens == 9:
                logger.error("Нет токенов с балансом для свапов!")
                logger.success(f'Выполнено свапов: {swaps}! Данные записаны в таблицу OGLabsActivity.xlsx')
                return
            random_sleep(5, 10)
            bot.ads.page.locator("svg.tabler-icon.tabler-icon-chevron-down").nth(0).click()
            random_sleep(3, 5)
            token_out.click()
            random_sleep(3, 5)
            bot.ads.page.get_by_role('button', name='MAX').click()
            random_sleep(3, 5)
            if bot.ads.page.get_by_role('button', name='Enter an amount').count() or bot.ads.page.get_by_role('button',
                                                                                                  name='Insufficient').count():
                no_balance_tokens += 1
                continue

            random_sleep(3, 5)

            if bot.ads.page.get_by_role('button', name='Approve').count():
                bot.ads.page.get_by_role('button', name='Approve').click()
                random_sleep(3, 5)
                bot.metamask.universal_confirm(windows=2, buttons=2)
                for _ in range(3):
                    if not bot.ads.page.locator('div.m_a49ed24.zer0dex-Notification-body',
                                                has_text='Waiting for confirmation...').count():
                        random_sleep(3, 5)
                        bot.ads.page.get_by_role('button', name='Approve').click()
                        random_sleep(3, 5)
                        bot.metamask.universal_confirm(windows=2, buttons=2)
                        break
                    random_sleep(3, 5)
                else:
                    logger.error('Ошибка транзакции Approve!')
                    return

                for _ in range(50):
                    if (not bot.ads.page.locator('div.m_a49ed24.zer0dex-Notification-body',
                                                 has_text='Waiting for confirmation...').count()
                            and bot.ads.page.get_by_role('button', name='Swap').count()):
                        break
                    random_sleep(5, 10)
                else:
                    logger.error('Ошибка транзакции Approve!')
                    return

            bot.ads.page.get_by_role('button', name='Swap').click()
            random_sleep(3, 5)
            bot.metamask.universal_confirm(windows=2, buttons=2)

            for _ in range(3):
                if not bot.ads.page.locator('div.m_a49ed24.zer0dex-Notification-body', has_text='Transaction is being submitted...').count():
                    bot.ads.page.get_by_role('button', name='Swap').click()
                    random_sleep(3, 5)
                    bot.metamask.universal_confirm(windows=2, buttons=2)
                    break
                random_sleep(3, 5)
            else:
                logger.error('Ошибка транзакции Swap!')
                return

            for _ in range(50):
                if not bot.ads.page.locator('div.m_a49ed24.zer0dex-Notification-body', has_text='Transaction is being submitted...').count():
                    break
                random_sleep(5, 10)
            else:
                logger.error('Ошибка транзакции Swap!')
                return

            excel_report.increase_counter(f'Zer0 Swaps')
            swaps += 1

            if swaps >= random_count:
                logger.success(f'Выполнено свапов: {swaps}! Данные записаны в таблицу OGLabsActivity.xlsx')
                break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')


