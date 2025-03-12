import random
from loguru import logger
from config import config, Chains
from core.bot import Bot
from core.excel import Excel
from core.onchain import Onchain
from models.account import Account
from models.amount import Amount
from utils.inputs import input_pause
from utils.logging import init_logger
from utils.utils import (random_sleep, get_accounts, select_profiles, get_user_agent)


def main():

    init_logger()
    accounts = get_accounts()
    accounts_for_work = select_profiles(accounts)
    pause = input_pause()

    for i in range(config.cycle):
        random.shuffle(accounts_for_work)
        for account in accounts_for_work:
            worker(account)
            random_sleep(pause)
        logger.success(f'Цикл {i + 1} завершен, обработано {len(accounts_for_work)} аккаунтов!')
        logger.info(f'Ожидание перед следующим циклом ~{config.pause_between_cycle[1]} секунд!')
        random_sleep(*config.pause_between_cycle)

def worker(account: Account) -> None:

    try:
        with Bot(account) as bot:
            activity(bot)
    except Exception as e:
        logger.critical(f"{account.profile_number} Ошибка при инициализации Bot: {e}")

def activity(bot: Bot):

    get_user_agent()
    excel_report = Excel(bot.account, file='OGLabsActivity.xlsx')
    excel_report.set_cell('Address', f'{bot.account.address}')
    domain_name = bot.excel.get_cell('Gmail').replace("@gmail.com", "")
    domain_name = domain_name.lower()
    hex_domain_name = domain_name.encode().hex()
    padded_hex_domain = hex_domain_name.ljust(64, '0')
    length = len(domain_name)
    length_hex = format(length, '02x')
    excel_report.set_date('Date')
    bot.onchain.change_chain(Chains.OGLABS_TESTNET)
    conft_domain_address = '0xCF7f37B4916AC5c530C863f8c8bB26Ec1e8d2Ccb'
    amount = Amount(0)
    tx = bot.onchain._prepare_tx(value=amount, to_address=conft_domain_address)
    tx['data'] = f'0x692b395600000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000{length_hex}{padded_hex_domain}'
    bot.onchain._estimate_gas(tx)
    tx_hash = bot.onchain._sign_and_send(tx)
    logger.info(f'Транзакция отправлена! Данные занесены в таблицу OGLabsActivity.xlsx! Hash: {tx_hash}')
    excel_report.increase_counter(f'Conft Domain')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning('Программа завершена вручную!')