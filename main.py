import re
from configparser import ConfigParser
from pyzabbix import ZabbixAPI
import telebot

config = ConfigParser()
config.read('config.ini')

# Autenticação no zabbix
zapi = ZabbixAPI(config.get('zabbix', 'url'))
zapi.login(config.get('zabbix', 'user'), config.get('zabbix', 'password'))

# Autenticação bot telegram
bot = telebot.TeleBot(config.get('telegram', 'token'), parse_mode='Markdown')


# Mensagem padrão com lista de comandos
@bot.message_handler(commands=['start'])
def start(mensagem):

    mensagem_padrao = '*Segue a lista de comandos: *\n\n'
    mensagem_padrao += '*/alertas* _<aviso | media | alta | desastre>_ - Lista todos incidentes por gravidade \n'
    mensagem_padrao += '*/vlan* _vlan-id_ - Mostra quantidade de logados na vlan'

    bot.send_message(mensagem.chat.id, mensagem_padrao)


# Consulta quantidade de clientes na VLAN
@bot.message_handler(commands='vlan')
def vlan(mensagem):

    vlan = mensagem.text
    vlan = re.sub("\/vlan |", "", vlan)

    items = zapi.item.get(
        output = 'extend',
        search = {
            'name': 'Quant-Clientes-Vlan-' + vlan
        }
    )

    for item in items:
        msg = '*VLAN ' + vlan + ':* \n' + item['lastvalue'] + ' clientes online'
        bot.send_message(mensagem.chat.id, msg)


# Retorna 5 incidentes,  filtrando por gravidade
@bot.message_handler(commands='alertas')
def alertas(mensagem):

    gravidade = mensagem.text
    gravidade = re.sub("\/alertas |", "", gravidade)

    if gravidade == 'aviso' :
        severidade = 2
    elif gravidade == 'media':
        severidade = 3
    elif gravidade == 'alta':
        severidade = 4
    elif gravidade == 'desastre':
        severidade = 5

    eventos = zapi.problem.get(
        output = 'extend',
        limit = 5,
        severities = severidade,
        sortfield = ['eventid'],
        sortorder = 'DESC'
    )

    for alerta in eventos:
        bot.send_message(mensagem.chat.id, '❌ '+alerta['name']+' ❌')


bot.polling()