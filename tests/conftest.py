"""Fuso fixo: os testes do Moodle esperam datas locais de Brasilia (timestamp 1778122740 = 2026-05-06)."""
import os
import time

os.environ["TZ"] = "America/Sao_Paulo"
if hasattr(time, "tzset"):  # ausente no Windows, onde o fuso do sistema ja e o do dono
    time.tzset()
