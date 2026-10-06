# Umamusume Project

Учебный прототип АИС клуба любителей скачек «Умамусуме» для лабораторной работы №2 по дисциплине «Автоматизация процессов жизненного цикла программных средств».

## Возможности

- учет владельцев;
- учет лошадей;
- учет жокеев;
- учет состязаний;
- регистрация результатов;
- сводная главная страница;
- SQLite создается и заполняется тестовыми данными при первом запуске.

## Запуск на Ubuntu

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv
git clone https://github.com/sqwirex/umamusume-project.git
cd umamusume-project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Приложение запускается на `0.0.0.0:5000`.

## Повторный запуск

```bash
cd umamusume-project
source .venv/bin/activate
python app.py
```
CI check prod 2026-10-06-21:45:56
