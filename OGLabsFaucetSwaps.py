
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
    bot.ads.open_url('https://hub.0g.ai/portfolio/token')
    random_sleep(5, 10)
    connect_button = bot.ads.page.get_by_role('button', name='Connect')
    if connect_button.count():
        bot.ads.page.get_by_role('button', name='Connect').nth(0).click()
        random_sleep(2, 3)
        bot.ads.page.get_by_text('MetaMask').click()
        bot.metamask.universal_confirm()
        random_sleep(2, 3)

    '''FAUCETS'''
    bot.ads.page.get_by_text("local_drink").click()
    random_sleep(20, 30)
    for _ in range(100):
        if bot.ads.page.get_by_role('button', name='Request A0GI', exact=True).is_enabled():
            random_sleep(5, 10)
            bot.ads.page.get_by_role('button', name='Request A0GI', exact=True).click()
            excel_report.increase_counter(f'Faucet A0GI')
            break
        random_sleep(5, 10)

    random_sleep(20, 30)

    bot.ads.page.locator('div.x-input-container').click()
    bot.ads.page.locator('span.text.font-bold', has_text='USDT').click()
    bot.ads.page.get_by_role('button', name='Request USDT', exact=True).click()
    bot.metamask.universal_confirm()
    excel_report.increase_counter(f'Faucet USDT')
    random_sleep(10, 20)

    bot.ads.page.locator('div.x-input-container').click()
    bot.ads.page.locator('span.text.font-bold', has_text='BTC').click()
    bot.ads.page.get_by_role('button', name='Request BTC', exact=True).click()
    bot.metamask.universal_confirm()
    excel_report.increase_counter(f'Faucet BTC')
    random_sleep(10, 20)

    bot.ads.page.locator('div.x-input-container').click()
    bot.ads.page.locator('span.text.font-bold', has_text='ETH').click()
    bot.ads.page.get_by_role('button', name='Request ETH', exact=True).click()
    bot.metamask.universal_confirm()
    excel_report.increase_counter(f'Faucet ETH')

    logger.success('Faucet активность завершена! Данные записаны в таблицу OGLabsActivity.xlsx')

    '''SWAPS'''
    bot.ads.page.get_by_text("swap_horizontal_circle").click()
    random_sleep(5, 10)
    USDT_token = bot.ads.page.locator("div.bc-title-wrapper").filter(has_text="USDT")
    ETH_token = bot.ads.page.locator("div.bc-title-wrapper").filter(has_text="ETH")
    BTC_token = bot.ads.page.locator("div.bc-title-wrapper").filter(has_text="BTC")

    tokens_out = [USDT_token, ETH_token, BTC_token]
    tokens_in = [USDT_token, ETH_token, BTC_token]
    swaps = 0
    random_count = random.randint(5, 10)
    while swaps < random_count:
        for token_out in tokens_out:
            random_sleep(5, 10)
            bot.ads.page.locator("span.material-icons-round", has_text="expand_more").nth(0).click()
            token_out.click()
            random_sleep(5, 10)

            if bot.ads.page.locator("span.badge.text-gray.font-bold").filter(has_text="MAX").count():
                continue

            if bot.ads.page.locator("p.text-center.font-bold").filter(has_text="Insufficient").count():
                continue

            bot.ads.page.locator("span.material-icons-round", has_text="expand_more").nth(1).click()

            for token_in in tokens_in:
                if token_in == token_out:
                    continue
                token_in.click()

                if not bot.ads.page.locator("p.text-center.font-bold").filter(has_text="Swap").count():
                    bot.ads.page.locator("span.material-icons-round", has_text="expand_more").nth(1).click()
                    continue
                else:
                    break

            random_sleep(5, 10)
            bot.ads.page.locator("span.badge.font-bold").filter(has_text="MAX").click()

            random_sleep(5, 10)
            if bot.ads.page.locator("p.text-center.font-bold").filter(has_text="Swap").count():
                bot.ads.page.locator("p.text-center.font-bold").filter(has_text="Swap").click()
                bot.metamask.universal_confirm(windows=3, buttons=3)
                random_sleep(10, 20)
                while True:
                    if bot.ads.page.locator("p.text-center.font-bold").filter(
                            has_text="Swap").count() or bot.ads.page.locator("p.text-center.font-bold").filter(
                            has_text="Insufficient").count():
                        break

                excel_report.increase_counter(f'Swaps')
                swaps += 1

            if swaps >= random_count:
                logger.success(f'Выполнено {random_count} свапов! Данные записаны в таблицу OGLabsActivity.xlsx')
                break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')


