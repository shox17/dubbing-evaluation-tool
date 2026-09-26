"""Interface text in English, Korean, Portuguese (Brazil) and Spanish.

TEXT holds every string app.py shows, keyed by a short id. MESSAGES translates the fixed English progress
messages that src/ reports (Perso steps, pipeline and evaluation steps); anything else stays in English.
Placeholders like {n} are filled with str.format, so every translation must use the same placeholders.
"""
from typing import Optional

UI_LANGUAGES = {"en": "English", "ko": "한국어", "pt": "Português", "es": "Español"}
DEFAULT_UI_LANGUAGE = "en"

TEXT = {
    # ----- sidebar -----
    "app.tagline": {
        "en": "Dub a video with Perso AI, then see how the dub compares to the original.",
        "ko": "Perso AI로 영상을 더빙하고, 더빙이 원본과 얼마나 잘 맞는지 확인하세요.",
        "pt": "Duble um vídeo com a Perso AI e veja como a dublagem se compara ao original.",
        "es": "Dobla un video con Perso AI y compara el doblaje con el original.",
    },
    "ui_language": {"en": "Interface language", "ko": "화면 언어", "pt": "Idioma da interface",
                    "es": "Idioma de la interfaz"},
    "account.title": {"en": "Perso account", "ko": "Perso 계정", "pt": "Conta Perso", "es": "Cuenta de Perso"},
    "account.demo_hint": {
        "en": "You can still try the free demo with the sample video.",
        "ko": "샘플 영상으로 무료 데모는 계속 사용할 수 있습니다.",
        "pt": "Você ainda pode usar a demonstração gratuita com o vídeo de exemplo.",
        "es": "Aún puedes probar la demostración gratuita con el video de ejemplo.",
    },
    "account.no_workspace": {
        "en": "Your Perso account has no workspace yet. Create one at perso.ai.",
        "ko": "Perso 계정에 아직 워크스페이스가 없습니다. perso.ai에서 만드세요.",
        "pt": "Sua conta Perso ainda não tem um espaço de trabalho. Crie um em perso.ai.",
        "es": "Tu cuenta de Perso aún no tiene un espacio de trabajo. Crea uno en perso.ai.",
    },
    "account.workspace": {"en": "Workspace", "ko": "워크스페이스", "pt": "Espaço de trabalho",
                          "es": "Espacio de trabajo"},
    "account.connected": {"en": "Connected", "ko": "연결됨", "pt": "Conectado", "es": "Conectado"},
    "account.plan": {"en": "Plan", "ko": "요금제", "pt": "Plano", "es": "Plan"},
    "account.credits_left": {"en": "Credits left", "ko": "남은 크레딧", "pt": "Créditos restantes",
                             "es": "Créditos restantes"},
    "account.credits_help": {
        "en": "Read live from Perso. Refreshes every minute and after each run.",
        "ko": "Perso에서 실시간으로 불러옵니다. 1분마다, 그리고 실행이 끝날 때마다 새로 고칩니다.",
        "pt": "Lido em tempo real da Perso. Atualiza a cada minuto e após cada execução.",
        "es": "Se lee en tiempo real de Perso. Se actualiza cada minuto y después de cada ejecución.",
    },
    "account.refresh": {"en": "Refresh balance", "ko": "잔액 새로 고침", "pt": "Atualizar saldo",
                        "es": "Actualizar saldo"},
    "account.free_plan": {
        "en": "Free plans can't download dubbed videos, so they can't be evaluated here.",
        "ko": "무료 요금제는 더빙된 영상을 다운로드할 수 없어 여기서 평가할 수 없습니다.",
        "pt": "Planos gratuitos não podem baixar vídeos dublados, então não podem ser avaliados aqui.",
        "es": "Los planes gratuitos no pueden descargar videos doblados, así que no se pueden evaluar aquí.",
    },
    "settings.title": {"en": "Settings", "ko": "설정", "pt": "Configurações", "es": "Configuración"},
    "settings.whisper": {"en": "Speech recognition model", "ko": "음성 인식 모델",
                         "pt": "Modelo de reconhecimento de fala", "es": "Modelo de reconocimiento de voz"},
    "settings.whisper_help": {
        "en": "Used to transcribe both videos. Larger models are more accurate but slower.",
        "ko": "두 영상을 받아쓰는 데 사용합니다. 큰 모델일수록 정확하지만 느립니다.",
        "pt": "Usado para transcrever os dois vídeos. Modelos maiores são mais precisos, porém mais lentos.",
        "es": "Se usa para transcribir ambos videos. Los modelos más grandes son más precisos, pero más lentos.",
    },
    "how.title": {"en": "How it works", "ko": "작동 방식", "pt": "Como funciona", "es": "Cómo funciona"},
    "how.body": {
        "en": "1. **Upload** your video to Perso AI.\n"
              "2. Perso **dubs** it into the target language and, if chosen, **re-renders the lips**.\n"
              "3. The app **waits** until Perso is done and downloads the result.\n"
              "4. Both videos are **measured**: timing, loudness, silence, what is actually said "
              "(speech recognition) and lip movement.\n"
              "5. You get an **original vs dubbed** comparison.",
        "ko": "1. 영상을 Perso AI에 **업로드**합니다.\n"
              "2. Perso가 대상 언어로 **더빙**하고, 선택한 경우 **입 모양을 다시 렌더링**합니다.\n"
              "3. 앱은 Perso가 끝날 때까지 **기다린** 뒤 결과를 다운로드합니다.\n"
              "4. 두 영상을 **측정**합니다: 타이밍, 음량, 무음, 실제로 말한 내용(음성 인식), 입 움직임.\n"
              "5. **원본과 더빙**을 비교한 결과를 받습니다.",
        "pt": "1. **Envie** seu vídeo para a Perso AI.\n"
              "2. A Perso **dubla** o vídeo no idioma de destino e, se você escolher, **refaz os lábios**.\n"
              "3. O app **espera** a Perso terminar e baixa o resultado.\n"
              "4. Os dois vídeos são **medidos**: tempo, volume, silêncio, o que é realmente dito "
              "(reconhecimento de fala) e movimento dos lábios.\n"
              "5. Você recebe uma comparação **original vs dublado**.",
        "es": "1. **Sube** tu video a Perso AI.\n"
              "2. Perso lo **dobla** al idioma de destino y, si lo eliges, **vuelve a generar los labios**.\n"
              "3. La app **espera** a que Perso termine y descarga el resultado.\n"
              "4. Se **miden** ambos videos: tiempos, volumen, silencio, lo que realmente se dice "
              "(reconocimiento de voz) y el movimiento de los labios.\n"
              "5. Obtienes una comparación **original vs doblado**.",
    },
    "sidebar.last_result": {"en": "Show last result", "ko": "마지막 결과 보기", "pt": "Mostrar último resultado",
                            "es": "Ver último resultado"},

    # ----- stages (progress checklist) -----
    "stage.upload": {"en": "Upload video to Perso", "ko": "Perso에 영상 업로드", "pt": "Enviar vídeo para a Perso",
                     "es": "Subir el video a Perso"},
    "stage.dubbing": {"en": "Dub the voice", "ko": "음성 더빙", "pt": "Dublar a voz", "es": "Doblar la voz"},
    "stage.lipsync": {"en": "Lip-sync the video", "ko": "영상 립싱크", "pt": "Sincronizar os lábios",
                      "es": "Sincronizar los labios"},
    "stage.download": {"en": "Download the dubbed video", "ko": "더빙된 영상 다운로드", "pt": "Baixar o vídeo dublado",
                       "es": "Descargar el video doblado"},
    "stage.evaluate": {"en": "Measure quality", "ko": "품질 측정", "pt": "Medir a qualidade", "es": "Medir la calidad"},

    # ----- time -----
    "time.min_sec": {"en": "{m} min {s} s", "ko": "{m}분 {s}초", "pt": "{m} min {s} s", "es": "{m} min {s} s"},
    "time.sec": {"en": "{s} s", "ko": "{s}초", "pt": "{s} s", "es": "{s} s"},

    # ----- progress page -----
    "progress.title": {"en": "Dubbing in progress", "ko": "더빙 진행 중", "pt": "Dublagem em andamento",
                       "es": "Doblaje en curso"},
    "progress.with_lipsync": {"en": " · with lip-sync", "ko": " · 립싱크 포함", "pt": " · com sincronização labial",
                              "es": " · con sincronización labial"},
    "progress.overall": {"en": "Overall", "ko": "전체", "pt": "Total", "es": "Total"},
    "progress.elapsed": {"en": "Elapsed", "ko": "경과 시간", "pt": "Tempo decorrido", "es": "Tiempo transcurrido"},
    "progress.time_left": {"en": "Time left", "ko": "남은 시간", "pt": "Tempo restante", "es": "Tiempo restante"},
    "progress.about_min": {"en": "about {n} min", "ko": "약 {n}분", "pt": "cerca de {n} min", "es": "unos {n} min"},
    "progress.about_min_left": {"en": "about {n} min left", "ko": "약 {n}분 남음", "pt": "faltam cerca de {n} min",
                                "es": "quedan unos {n} min"},
    "progress.lipsync_info": {
        "en": "Lip-sync re-renders every frame of the video, so this is the slowest step "
              "(often 5–30 minutes). The results appear here automatically when it's done.",
        "ko": "립싱크는 영상의 모든 프레임을 다시 렌더링하므로 가장 느린 단계입니다(보통 5–30분). "
              "완료되면 결과가 여기에 자동으로 표시됩니다.",
        "pt": "A sincronização labial refaz cada quadro do vídeo, por isso é a etapa mais lenta "
              "(geralmente 5–30 minutos). Os resultados aparecem aqui automaticamente quando terminar.",
        "es": "La sincronización labial vuelve a generar cada fotograma del video, así que es el paso más lento "
              "(suele tardar 5–30 minutos). Los resultados aparecerán aquí automáticamente al terminar.",
    },
    "progress.leave_hint": {
        "en": "You can leave this tab open and come back. Reloading the page is safe; "
              "stopping the app server stops the tracking (the Perso job itself keeps running).",
        "ko": "이 탭을 열어 두고 나중에 돌아와도 됩니다. 페이지를 새로 고쳐도 괜찮지만, "
              "앱 서버를 중지하면 추적이 멈춥니다(Perso 작업 자체는 계속 실행됩니다).",
        "pt": "Você pode deixar esta aba aberta e voltar depois. Recarregar a página é seguro; "
              "parar o servidor do app interrompe o acompanhamento (o trabalho na Perso continua).",
        "es": "Puedes dejar esta pestaña abierta y volver más tarde. Recargar la página es seguro; "
              "detener el servidor de la app detiene el seguimiento (el trabajo en Perso sigue en marcha).",
    },
    "progress.stop": {"en": "Stop waiting", "ko": "기다리기 중지", "pt": "Parar de esperar", "es": "Dejar de esperar"},
    "progress.stop_help": {
        "en": "Cancels the Perso job if it is still queued. Jobs that already started may still use credits.",
        "ko": "대기 중인 Perso 작업을 취소합니다. 이미 시작된 작업은 크레딧이 사용될 수 있습니다.",
        "pt": "Cancela o trabalho na Perso se ainda estiver na fila. Trabalhos já iniciados ainda podem usar créditos.",
        "es": "Cancela el trabajo en Perso si aún está en cola. Los trabajos ya iniciados pueden seguir usando créditos.",
    },
    "progress.stopping": {"en": "Stopping... this takes a few seconds.", "ko": "중지하는 중... 몇 초 걸립니다.",
                          "pt": "Parando... isso leva alguns segundos.", "es": "Deteniendo... tarda unos segundos."},

    # ----- results page -----
    "results.title": {"en": "Results", "ko": "결과", "pt": "Resultados", "es": "Resultados"},
    "results.download": {"en": "Download report", "ko": "보고서 다운로드", "pt": "Baixar relatório",
                         "es": "Descargar informe"},
    "results.download_help": {"en": "The full measurements as a JSON file.", "ko": "모든 측정값을 담은 JSON 파일입니다.",
                              "pt": "Todas as medições em um arquivo JSON.",
                              "es": "Todas las mediciones en un archivo JSON."},
    "results.new": {"en": "New evaluation", "ko": "새 평가", "pt": "Nova avaliação", "es": "Nueva evaluación"},
    "results.things_to_check": {"en": "Things to check", "ko": "확인할 사항", "pt": "Pontos a verificar",
                                "es": "Cosas que revisar"},
    "results.original": {"en": "Original", "ko": "원본", "pt": "Original", "es": "Original"},
    "results.dubbed": {"en": "Dubbed", "ko": "더빙", "pt": "Dublado", "es": "Doblado"},
    "results.video_gone": {
        "en": "The dubbed video file is no longer on disk (old runs are cleaned up).",
        "ko": "더빙된 영상 파일이 더 이상 디스크에 없습니다(오래된 실행은 정리됩니다).",
        "pt": "O arquivo do vídeo dublado não está mais no disco (execuções antigas são apagadas).",
        "es": "El archivo del video doblado ya no está en el disco (las ejecuciones antiguas se eliminan).",
    },
    "results.at_a_glance": {"en": "At a glance", "ko": "한눈에 보기", "pt": "Resumo", "es": "Resumen"},
    "badge.good": {"en": "Good", "ko": "좋음", "pt": "Bom", "es": "Bien"},
    "badge.check": {"en": "Check", "ko": "확인 필요", "pt": "Verificar", "es": "Revisar"},
    "badge.poor": {"en": "Poor", "ko": "미흡", "pt": "Ruim", "es": "Deficiente"},
    "badge.info": {"en": "Experimental", "ko": "실험적", "pt": "Experimental", "es": "Experimental"},
    "badge.na": {"en": "Not scored", "ko": "점수 없음", "pt": "Sem pontuação", "es": "Sin puntuación"},
    "card.timing": {"en": "Timing match", "ko": "길이 일치", "pt": "Duração", "es": "Duración"},
    "card.timing_caption": {
        "en": "Dub is {dub} s vs {orig} s original. Should be close to 0.",
        "ko": "더빙 {dub}초, 원본 {orig}초. 0에 가까울수록 좋습니다.",
        "pt": "A dublagem tem {dub} s e o original {orig} s. O ideal é perto de 0.",
        "es": "El doblaje dura {dub} s y el original {orig} s. Lo ideal es cerca de 0.",
    },
    "card.script": {"en": "Matches your script", "ko": "스크립트 일치", "pt": "Fidelidade ao roteiro",
                    "es": "Coincide con tu guion"},
    "card.script_caption": {
        "en": "How much of your script is heard in the dub. Different wording also lowers it; "
              "see “What was said” below.",
        "ko": "더빙에서 스크립트가 얼마나 들리는지입니다. 표현이 달라도 점수가 낮아지니 아래 “실제로 말한 내용”을 확인하세요.",
        "pt": "Quanto do seu roteiro é ouvido na dublagem. Palavras diferentes também baixam a nota; "
              "veja “O que foi dito” abaixo.",
        "es": "Cuánto de tu guion se escucha en el doblaje. Una redacción distinta también lo baja; "
              "consulta “Lo que se dijo” más abajo.",
    },
    "card.script_none": {
        "en": "Enter a target script next time to get this score.",
        "ko": "다음에 대상 스크립트를 입력하면 이 점수를 받을 수 있습니다.",
        "pt": "Informe um roteiro na próxima vez para obter esta nota.",
        "es": "Escribe un guion la próxima vez para obtener esta puntuación.",
    },
    "card.clarity": {"en": "Voice clarity", "ko": "음성 명료도", "pt": "Clareza da voz", "es": "Claridad de la voz"},
    "card.clarity_caption": {
        "en": "How clearly the dubbed voice speaks Perso's own translation.",
        "ko": "더빙 음성이 Perso의 번역문을 얼마나 또렷하게 말하는지입니다.",
        "pt": "Quão claramente a voz dublada fala a própria tradução da Perso.",
        "es": "Qué tan claro dice la voz doblada la propia traducción de Perso.",
    },
    "card.loudness": {"en": "Loudness match", "ko": "음량 일치", "pt": "Volume", "es": "Volumen"},
    "card.loudness_caption": {
        "en": "Dub loudness vs the original. Within ±2 dB sounds the same.",
        "ko": "원본 대비 더빙 음량입니다. ±2 dB 이내면 같게 들립니다.",
        "pt": "Volume da dublagem em relação ao original. Até ±2 dB soa igual.",
        "es": "Volumen del doblaje frente al original. Dentro de ±2 dB suena igual.",
    },
    "card.lips": {"en": "Lip movement", "ko": "입 움직임", "pt": "Movimento dos lábios",
                  "es": "Movimiento de los labios"},
    "card.lips_caption": {
        "en": "Original video scores {r}. Compare the two; it is not an absolute score.",
        "ko": "원본 영상은 {r}입니다. 두 값을 비교하세요. 절대적인 점수가 아닙니다.",
        "pt": "O vídeo original marca {r}. Compare os dois; não é uma nota absoluta.",
        "es": "El video original obtiene {r}. Compara ambos; no es una puntuación absoluta.",
    },
    "card.lips_na": {"en": "Could not be measured.", "ko": "측정할 수 없습니다.", "pt": "Não foi possível medir.",
                     "es": "No se pudo medir."},
    "table.title": {"en": "Original vs dubbed", "ko": "원본 vs 더빙", "pt": "Original vs dublado",
                    "es": "Original vs doblado"},
    "table.measure": {"en": "Measure", "ko": "항목", "pt": "Medida", "es": "Medida"},
    "table.difference": {"en": "Difference", "ko": "차이", "pt": "Diferença", "es": "Diferencia"},
    "table.meaning": {"en": "What it means", "ko": "의미", "pt": "O que significa", "es": "Qué significa"},
    "row.duration": {"en": "Duration", "ko": "길이", "pt": "Duração", "es": "Duración"},
    "row.duration_help": {"en": "Total length. A good dub keeps the same length.",
                          "ko": "전체 길이입니다. 좋은 더빙은 길이가 같습니다.",
                          "pt": "Duração total. Uma boa dublagem mantém a mesma duração.",
                          "es": "Duración total. Un buen doblaje mantiene la misma duración."},
    "row.speaking": {"en": "Speaking time", "ko": "발화 시간", "pt": "Tempo de fala", "es": "Tiempo de habla"},
    "row.speaking_help": {"en": "Time with sound above the silence threshold.",
                          "ko": "무음 기준보다 큰 소리가 나는 시간입니다.",
                          "pt": "Tempo com som acima do limite de silêncio.",
                          "es": "Tiempo con sonido por encima del umbral de silencio."},
    "row.loudness": {"en": "Loudness", "ko": "음량", "pt": "Volume", "es": "Volumen"},
    "row.loudness_help": {"en": "Average volume. Within ±2 dB sounds the same.",
                          "ko": "평균 음량입니다. ±2 dB 이내면 같게 들립니다.",
                          "pt": "Volume médio. Até ±2 dB soa igual.",
                          "es": "Volumen medio. Dentro de ±2 dB suena igual."},
    "row.steadiness": {"en": "Volume steadiness", "ko": "음량 안정성", "pt": "Estabilidade do volume",
                       "es": "Estabilidad del volumen"},
    "row.steadiness_help": {"en": "Higher means a more even volume.", "ko": "높을수록 음량이 고릅니다.",
                            "pt": "Quanto maior, mais uniforme o volume.",
                            "es": "Cuanto más alto, más uniforme el volumen."},
    "row.silence": {"en": "Silence", "ko": "무음", "pt": "Silêncio", "es": "Silencio"},
    "row.silence_help": {"en": "Share of the video without sound.", "ko": "소리가 없는 구간의 비율입니다.",
                         "pt": "Parte do vídeo sem som.", "es": "Parte del video sin sonido."},
    "row.rate": {"en": "Speech rate", "ko": "말하기 속도", "pt": "Velocidade da fala", "es": "Velocidad del habla"},
    "row.rate_help": {"en": "How fast the speaker talks. Units differ per language, so compare with care.",
                      "ko": "말하는 속도입니다. 언어마다 단위가 달라 비교에 주의하세요.",
                      "pt": "A velocidade com que a pessoa fala. As unidades variam por idioma, compare com cuidado.",
                      "es": "Qué tan rápido habla la persona. Las unidades varían por idioma, compara con cuidado."},
    "row.lipsync": {"en": "Lip-sync r (experimental)", "ko": "립싱크 r (실험적)",
                    "pt": "Sincronização labial r (experimental)", "es": "Sincronización labial r (experimental)"},
    "row.lipsync_help": {"en": "Mouth opening vs voice loudness. Only meaningful relative to the original.",
                         "ko": "입 벌림과 음성 크기의 관계입니다. 원본과 비교할 때만 의미가 있습니다.",
                         "pt": "Abertura da boca vs volume da voz. Só faz sentido em relação ao original.",
                         "es": "Apertura de la boca frente al volumen de la voz. Solo tiene sentido frente al original."},
    "row.face": {"en": "Face visible", "ko": "얼굴 인식", "pt": "Rosto visível", "es": "Rostro visible"},
    "row.face_help": {"en": "Share of frames where a face was found.", "ko": "얼굴이 발견된 프레임의 비율입니다.",
                      "pt": "Parte dos quadros em que um rosto foi encontrado.",
                      "es": "Parte de los fotogramas en los que se encontró un rostro."},
    "unit.pts": {"en": "pts", "ko": "%p", "pt": "p.p.", "es": "p.p."},
    "unit.words/s": {"en": "words/s", "ko": "단어/초", "pt": "palavras/s", "es": "palabras/s"},
    "unit.chars/s": {"en": "chars/s", "ko": "글자/초", "pt": "caracteres/s", "es": "caracteres/s"},
    "chart.loudness_title": {"en": "Loudness over time", "ko": "시간에 따른 음량", "pt": "Volume ao longo do tempo",
                             "es": "Volumen a lo largo del tiempo"},
    "chart.seconds": {"en": "seconds", "ko": "초", "pt": "segundos", "es": "segundos"},
    "chart.loudness_caption": {
        "en": "Peaks should line up: speech in the dub should start and stop where the original does.",
        "ko": "봉우리가 겹쳐야 합니다. 더빙의 말소리가 원본과 같은 곳에서 시작하고 끝나야 합니다.",
        "pt": "Os picos devem se alinhar: a fala na dublagem deve começar e parar onde o original faz.",
        "es": "Los picos deben coincidir: el habla del doblaje debe empezar y terminar donde lo hace el original.",
    },
    "said.title": {"en": "What was said", "ko": "실제로 말한 내용", "pt": "O que foi dito", "es": "Lo que se dijo"},
    "said.tab_script": {"en": "Your script vs the dub", "ko": "내 스크립트 vs 더빙", "pt": "Seu roteiro vs dublagem",
                        "es": "Tu guion vs el doblaje"},
    "said.tab_perso": {"en": "Perso's translation", "ko": "Perso 번역", "pt": "Tradução da Perso",
                       "es": "Traducción de Perso"},
    "said.tab_original": {"en": "Original speech", "ko": "원본 음성", "pt": "Fala original", "es": "Habla original"},
    "said.legend": {
        "en": "Accuracy {acc} · {metric} {err} · :red-background[struck red] = in your script but not heard · "
              ":green-background[green] = heard but not in your script",
        "ko": "정확도 {acc} · {metric} {err} · :red-background[빨간 취소선] = 스크립트에 있지만 들리지 않음 · "
              ":green-background[초록] = 들렸지만 스크립트에 없음",
        "pt": "Precisão {acc} · {metric} {err} · :red-background[vermelho riscado] = no roteiro, mas não ouvido · "
              ":green-background[verde] = ouvido, mas não está no roteiro",
        "es": "Precisión {acc} · {metric} {err} · :red-background[rojo tachado] = en tu guion pero no se oye · "
              ":green-background[verde] = se oye pero no está en tu guion",
    },
    "said.diff_note": {
        "en": "Differences can come from the translation wording, speech-recognition mistakes, or real dubbing errors.",
        "ko": "차이는 번역 표현, 음성 인식 오류, 또는 실제 더빙 오류 때문일 수 있습니다.",
        "pt": "As diferenças podem vir das palavras da tradução, de erros do reconhecimento de fala "
              "ou de erros reais da dublagem.",
        "es": "Las diferencias pueden deberse a la redacción de la traducción, a errores del reconocimiento de voz "
              "o a errores reales del doblaje.",
    },
    "said.no_script": {"en": "No target script was entered for this run.",
                       "ko": "이번 실행에는 대상 스크립트가 입력되지 않았습니다.",
                       "pt": "Nenhum roteiro foi informado nesta execução.",
                       "es": "No se escribió un guion para esta ejecución."},
    "said.heard": {"en": "Heard in the dub:", "ko": "더빙에서 들린 내용:", "pt": "Ouvido na dublagem:",
                   "es": "Se oye en el doblaje:"},
    "said.perso_match": {
        "en": "Perso's translation matches your script {pct}% (differences here are wording choices, not voice problems).",
        "ko": "Perso의 번역이 스크립트와 {pct}% 일치합니다(여기서의 차이는 표현 선택이며 음성 문제가 아닙니다).",
        "pt": "A tradução da Perso corresponde {pct}% ao seu roteiro (as diferenças aqui são escolhas de palavras, "
              "não problemas de voz).",
        "es": "La traducción de Perso coincide un {pct}% con tu guion (las diferencias aquí son de redacción, "
              "no problemas de voz).",
    },
    "said.perso_live_only": {
        "en": "Perso's translated script is only available for live dubbing runs.",
        "ko": "Perso의 번역 스크립트는 실제 더빙 실행에서만 볼 수 있습니다.",
        "pt": "O roteiro traduzido da Perso só está disponível em dublagens reais.",
        "es": "El guion traducido de Perso solo está disponible en doblajes reales.",
    },
    "said.detected": {"en": "Detected language: `{lang}`", "ko": "감지된 언어: `{lang}`",
                      "pt": "Idioma detectado: `{lang}`", "es": "Idioma detectado: `{lang}`"},
    "lips.expander": {"en": "Lip movement details (experimental)", "ko": "입 움직임 상세 (실험적)",
                      "pt": "Detalhes do movimento dos lábios (experimental)",
                      "es": "Detalles del movimiento de los labios (experimental)"},
    "lips.mouth": {"en": "Mouth opening", "ko": "입 벌림", "pt": "Abertura da boca", "es": "Apertura de la boca"},
    "lips.voice": {"en": "Voice loudness", "ko": "음성 크기", "pt": "Volume da voz", "es": "Volumen de la voz"},
    "lips.caption": {
        "en": "When the lips match the voice, the two lines rise and fall together. This simple measure is "
              "easily confused by voice-over, cut-aways and background music, so compare the dub with the "
              "original rather than reading the number on its own.",
        "ko": "입이 목소리와 맞으면 두 선이 함께 오르내립니다. 이 간단한 측정은 내레이션, 장면 전환, 배경 음악에 "
              "쉽게 흔들리므로 숫자만 보지 말고 더빙을 원본과 비교하세요.",
        "pt": "Quando os lábios combinam com a voz, as duas linhas sobem e descem juntas. Esta medida simples se "
              "confunde facilmente com narração, cortes de cena e música de fundo, então compare a dublagem com o "
              "original em vez de ler o número sozinho.",
        "es": "Cuando los labios coinciden con la voz, las dos líneas suben y bajan juntas. Esta medida sencilla se "
              "confunde fácilmente con voz en off, cambios de plano y música de fondo, así que compara el doblaje "
              "con el original en lugar de leer el número por sí solo.",
    },

    # ----- setup page -----
    "setup.title": {"en": "Check the quality of a dubbed video", "ko": "더빙 영상 품질 확인",
                    "pt": "Verifique a qualidade de um vídeo dublado", "es": "Revisa la calidad de un video doblado"},
    "setup.intro": {
        "en": "Pick a video, choose the language, paste the script the dub should say, and press **Start**. "
              "The app waits for Perso AI to finish and then compares the dub with the original.",
        "ko": "영상을 고르고, 언어를 선택하고, 더빙이 말해야 할 스크립트를 붙여 넣은 뒤 **시작**을 누르세요. "
              "앱이 Perso AI가 끝날 때까지 기다렸다가 더빙을 원본과 비교합니다.",
        "pt": "Escolha um vídeo e o idioma, cole o roteiro que a dublagem deve dizer e clique em **Iniciar**. "
              "O app espera a Perso AI terminar e depois compara a dublagem com o original.",
        "es": "Elige un video y el idioma, pega el guion que debe decir el doblaje y pulsa **Iniciar**. "
              "La app espera a que Perso AI termine y luego compara el doblaje con el original.",
    },
    "step1.title": {"en": "① Choose a video", "ko": "① 영상 선택", "pt": "① Escolha um vídeo", "es": "① Elige un video"},
    "source.sample": {"en": "Use the sample video", "ko": "샘플 영상 사용", "pt": "Usar o vídeo de exemplo",
                      "es": "Usar el video de ejemplo"},
    "source.upload": {"en": "Upload my own video", "ko": "내 영상 업로드", "pt": "Enviar meu próprio vídeo",
                      "es": "Subir mi propio video"},
    "upload.label": {"en": "Video file", "ko": "영상 파일", "pt": "Arquivo de vídeo", "es": "Archivo de video"},
    "upload.help": {"en": "Perso accepts MP4, MOV and WebM, up to 2 GB.",
                    "ko": "Perso는 최대 2 GB의 MP4, MOV, WebM 파일을 받습니다.",
                    "pt": "A Perso aceita MP4, MOV e WebM, até 2 GB.",
                    "es": "Perso acepta MP4, MOV y WebM, de hasta 2 GB."},
    "upload.earlier": {"en": "Using your earlier upload: `{name}`", "ko": "이전에 업로드한 파일 사용: `{name}`",
                       "pt": "Usando o envio anterior: `{name}`", "es": "Usando tu archivo anterior: `{name}`"},
    "sample.caption": {"en": "A 29-second English vlog. Good for a first try.",
                       "ko": "29초 길이의 영어 브이로그입니다. 처음 써 보기에 좋습니다.",
                       "pt": "Um vlog de 29 segundos em inglês. Bom para começar.",
                       "es": "Un vlog de 29 segundos en inglés. Ideal para una primera prueba."},
    "video.unreadable": {"en": "This file can't be read as a video. Try another file.",
                         "ko": "이 파일은 영상으로 읽을 수 없습니다. 다른 파일을 사용해 보세요.",
                         "pt": "Este arquivo não pode ser lido como vídeo. Tente outro arquivo.",
                         "es": "Este archivo no se puede leer como video. Prueba con otro archivo."},
    "step2.title": {"en": "② Choose the dubbing options", "ko": "② 더빙 옵션 선택",
                    "pt": "② Escolha as opções de dublagem", "es": "② Elige las opciones de doblaje"},
    "dub_into": {"en": "Dub into", "ko": "더빙 언어", "pt": "Dublar para", "es": "Doblar a"},
    "dub_into_help": {"en": "All {n} languages Perso can dub into. Type to search.",
                      "ko": "Perso가 더빙할 수 있는 {n}개 언어 전체입니다. 입력해서 검색하세요.",
                      "pt": "Todos os {n} idiomas para os quais a Perso dubla. Digite para buscar.",
                      "es": "Los {n} idiomas a los que Perso puede doblar. Escribe para buscar."},
    "experimental_suffix": {"en": " (experimental)", "ko": " (실험적)", "pt": " (experimental)",
                            "es": " (experimental)"},
    "no_whisper": {
        "en": "Speech recognition doesn't support {lang}, so the script scores will be rough.",
        "ko": "음성 인식이 지원하지 않는 언어({lang})라서 스크립트 점수는 대략적인 값입니다.",
        "pt": "O reconhecimento de fala não suporta {lang}, então as notas do roteiro serão aproximadas.",
        "es": "El reconocimiento de voz no admite {lang}, así que las puntuaciones del guion serán aproximadas.",
    },
    "lipsync.toggle": {"en": "Lip-sync the video", "ko": "영상 립싱크", "pt": "Sincronizar os lábios do vídeo",
                       "es": "Sincronizar los labios del video"},
    "lipsync.help": {
        "en": "Perso re-renders the speaker's lips to match the new language. "
              "Looks more natural but costs about twice the credits and takes much longer.",
        "ko": "Perso가 새 언어에 맞게 화자의 입 모양을 다시 렌더링합니다. "
              "더 자연스럽지만 크레딧이 약 두 배 들고 시간이 훨씬 오래 걸립니다.",
        "pt": "A Perso refaz os lábios de quem fala para combinar com o novo idioma. "
              "Fica mais natural, mas custa cerca do dobro de créditos e demora bem mais.",
        "es": "Perso vuelve a generar los labios de quien habla para que coincidan con el nuevo idioma. "
              "Se ve más natural, pero cuesta cerca del doble de créditos y tarda mucho más.",
    },
    "demo.toggle": {
        "en": "Free demo: use a ready-made Korean dub (no credits, about 30 s)",
        "ko": "무료 데모: 미리 만든 한국어 더빙 사용(크레딧 없음, 약 30초)",
        "pt": "Demonstração gratuita: usar uma dublagem pronta em coreano (sem créditos, cerca de 30 s)",
        "es": "Demostración gratuita: usar un doblaje al coreano ya hecho (sin créditos, unos 30 s)",
    },
    "demo.help": {
        "en": "Skips Perso and evaluates a Korean dub of the sample video that was made earlier.",
        "ko": "Perso를 건너뛰고, 미리 만들어 둔 샘플 영상의 한국어 더빙을 평가합니다.",
        "pt": "Pula a Perso e avalia uma dublagem em coreano do vídeo de exemplo feita antes.",
        "es": "Omite Perso y evalúa un doblaje al coreano del video de ejemplo hecho anteriormente.",
    },
    "cost.free": {"en": "Cost: **free** (demo)", "ko": "비용: **무료**(데모)", "pt": "Custo: **grátis** (demonstração)",
                  "es": "Costo: **gratis** (demostración)"},
    "cost.estimate": {"en": "Estimated cost: **{est} credits** · you have {have}",
                      "ko": "예상 비용: **{est} 크레딧** · 보유 {have}",
                      "pt": "Custo estimado: **{est} créditos** · você tem {have}",
                      "es": "Costo estimado: **{est} créditos** · tienes {have}"},
    "cost.not_enough": {"en": ". Not enough credits: top up at perso.ai or turn off lip-sync.",
                        "ko": ". 크레딧이 부족합니다. perso.ai에서 충전하거나 립싱크를 끄세요.",
                        "pt": ". Créditos insuficientes: recarregue em perso.ai ou desative a sincronização labial.",
                        "es": ". Créditos insuficientes: recarga en perso.ai o desactiva la sincronización labial."},
    "step3.title": {"en": "③ Paste the target script", "ko": "③ 대상 스크립트 붙여 넣기", "pt": "③ Cole o roteiro",
                    "es": "③ Pega el guion"},
    "step3.caption": {
        "en": "Write what the dubbed video should say, **in {lang}**. After dubbing, the app listens "
              "to the dub and shows how much of this script is actually heard. Leave it empty to skip that score.",
        "ko": "더빙된 영상이 말해야 할 내용을 **{lang}** 언어로 적으세요. 더빙이 끝나면 앱이 더빙을 듣고 이 스크립트가 "
              "실제로 얼마나 들리는지 보여 줍니다. 비워 두면 이 점수는 건너뜁니다.",
        "pt": "Escreva o que o vídeo dublado deve dizer, **em {lang}**. Depois da dublagem, o app ouve a dublagem "
              "e mostra quanto deste roteiro é realmente ouvido. Deixe vazio para pular essa nota.",
        "es": "Escribe lo que debe decir el video doblado, **en {lang}**. Tras el doblaje, la app escucha el doblaje "
              "y muestra cuánto de este guion se oye realmente. Déjalo vacío para omitir esa puntuación.",
    },
    "script.paste_sample": {"en": "Paste the sample's Korean script", "ko": "샘플의 한국어 스크립트 붙여 넣기",
                            "pt": "Colar o roteiro em coreano do exemplo", "es": "Pegar el guion en coreano del ejemplo"},
    "script.placeholder": {"en": "Paste the {lang} script here...", "ko": "{lang} 스크립트를 여기에 붙여 넣으세요...",
                           "pt": "Cole o roteiro em {lang} aqui...", "es": "Pega aquí el guion en {lang}..."},
    "problem.video": {"en": "Choose a video in step ①.", "ko": "① 단계에서 영상을 선택하세요.",
                      "pt": "Escolha um vídeo na etapa ①.", "es": "Elige un video en el paso ①."},
    "problem.account": {"en": "Connect a Perso account (see the sidebar), or use the free demo.",
                        "ko": "Perso 계정을 연결하거나(사이드바 참고) 무료 데모를 사용하세요.",
                        "pt": "Conecte uma conta Perso (veja a barra lateral) ou use a demonstração gratuita.",
                        "es": "Conecta una cuenta de Perso (mira la barra lateral) o usa la demostración gratuita."},
    "problem.free": {"en": "Free Perso plans can't download results. Upgrade the plan, or use the free demo.",
                     "ko": "Perso 무료 요금제는 결과를 다운로드할 수 없습니다. 요금제를 업그레이드하거나 무료 데모를 사용하세요.",
                     "pt": "Planos gratuitos da Perso não baixam resultados. Faça upgrade do plano ou use a demonstração gratuita.",
                     "es": "Los planes gratuitos de Perso no descargan resultados. Mejora el plan o usa la demostración gratuita."},
    "problem.credits": {"en": "Not enough Perso credits for this video.",
                        "ko": "이 영상에 필요한 Perso 크레딧이 부족합니다.",
                        "pt": "Créditos da Perso insuficientes para este vídeo.",
                        "es": "No hay suficientes créditos de Perso para este video."},
    "start.demo": {"en": "Start demo evaluation", "ko": "데모 평가 시작", "pt": "Iniciar avaliação de demonstração",
                   "es": "Iniciar evaluación de demostración"},
    "start.dub": {"en": "Start dubbing", "ko": "더빙 시작", "pt": "Iniciar dublagem", "es": "Iniciar doblaje"},
    "start.dub_cost": {"en": "Start dubbing ({est} credits)", "ko": "더빙 시작 ({est} 크레딧)",
                       "pt": "Iniciar dublagem ({est} créditos)", "es": "Iniciar doblaje ({est} créditos)"},

    # ----- stopped / failed jobs -----
    "stopped.title": {"en": "Dubbing stopped", "ko": "더빙이 중지되었습니다", "pt": "Dublagem interrompida",
                      "es": "Doblaje detenido"},
    "failed.title": {"en": "Something went wrong", "ko": "문제가 발생했습니다", "pt": "Algo deu errado",
                     "es": "Algo salió mal"},
    "stopped.during": {"en": "It stopped during: {stage} · after {time}", "ko": "중지된 단계: {stage} · {time} 후",
                       "pt": "Parou durante: {stage} · depois de {time}", "es": "Se detuvo en: {stage} · tras {time}"},
    "stopped.projects": {"en": "Perso project(s): ", "ko": "Perso 프로젝트: ", "pt": "Projeto(s) na Perso: ",
                         "es": "Proyecto(s) en Perso: "},
    "back": {"en": "Back to setup", "ko": "설정으로 돌아가기", "pt": "Voltar à configuração",
             "es": "Volver a la configuración"},
    "untracked": {
        "en": "That job is no longer being tracked (the app was restarted). Check your Perso workspace for the dubbed video.",
        "ko": "이 작업은 더 이상 추적되지 않습니다(앱이 다시 시작됨). 더빙된 영상은 Perso 워크스페이스에서 확인하세요.",
        "pt": "Esse trabalho não está mais sendo acompanhado (o app foi reiniciado). Procure o vídeo dublado "
              "no seu espaço de trabalho da Perso.",
        "es": "Ese trabajo ya no se está siguiendo (la app se reinició). Busca el video doblado en tu espacio "
              "de trabajo de Perso.",
    },
}

# Fixed English progress messages reported by src/ (Perso steps, pipeline and evaluation), translated by text.
MESSAGES = {
    "Starting...": {"ko": "시작하는 중...", "pt": "Iniciando...", "es": "Iniciando..."},
    "Finished": {"ko": "완료", "pt": "Concluído", "es": "Terminado"},
    "Waiting in the Perso queue": {"ko": "Perso 대기열에서 기다리는 중", "pt": "Aguardando na fila da Perso",
                                   "es": "Esperando en la cola de Perso"},
    "Waiting in the Perso queue (slow mode)": {"ko": "Perso 대기열에서 기다리는 중(저속 모드)",
                                               "pt": "Aguardando na fila da Perso (modo lento)",
                                               "es": "Esperando en la cola de Perso (modo lento)"},
    "Preparing media": {"ko": "미디어 준비 중", "pt": "Preparando a mídia", "es": "Preparando el contenido"},
    "Transcribing the original speech": {"ko": "원본 음성 받아쓰는 중", "pt": "Transcrevendo a fala original",
                                         "es": "Transcribiendo el habla original"},
    "Translating the script": {"ko": "스크립트 번역 중", "pt": "Traduzindo o roteiro", "es": "Traduciendo el guion"},
    "Generating the dubbed voice": {"ko": "더빙 음성 생성 중", "pt": "Gerando a voz dublada",
                                    "es": "Generando la voz doblada"},
    "Analyzing mouth movements": {"ko": "입 움직임 분석 중", "pt": "Analisando os movimentos da boca",
                                  "es": "Analizando los movimientos de la boca"},
    "Re-rendering lips to match the new audio": {"ko": "새 음성에 맞게 입 모양 다시 렌더링 중",
                                                 "pt": "Refazendo os lábios para combinar com o novo áudio",
                                                 "es": "Regenerando los labios para que coincidan con el nuevo audio"},
    "Completed": {"ko": "완료", "pt": "Concluído", "es": "Completado"},
    "Failed": {"ko": "실패", "pt": "Falhou", "es": "Falló"},
    "Checking the video against your Perso plan...": {"ko": "Perso 요금제 한도에 맞는지 영상 확인 중...",
                                                      "pt": "Verificando o vídeo com o seu plano da Perso...",
                                                      "es": "Comprobando el video con tu plan de Perso..."},
    "Sending the dubbing request...": {"ko": "더빙 요청 보내는 중...", "pt": "Enviando o pedido de dublagem...",
                                       "es": "Enviando la solicitud de doblaje..."},
    "Requesting lip-sync...": {"ko": "립싱크 요청 중...", "pt": "Solicitando a sincronização labial...",
                               "es": "Solicitando la sincronización labial..."},
    "Downloading the dubbed video...": {"ko": "더빙된 영상 다운로드 중...", "pt": "Baixando o vídeo dublado...",
                                        "es": "Descargando el video doblado..."},
    "Fetching Perso's translated script...": {"ko": "Perso 번역 스크립트 가져오는 중...",
                                              "pt": "Buscando o roteiro traduzido da Perso...",
                                              "es": "Obteniendo el guion traducido de Perso..."},
    "Loading the speech recognition model...": {"ko": "음성 인식 모델 불러오는 중...",
                                                "pt": "Carregando o modelo de reconhecimento de fala...",
                                                "es": "Cargando el modelo de reconocimiento de voz..."},
    "Extracting audio from both videos...": {"ko": "두 영상에서 오디오 추출 중...",
                                             "pt": "Extraindo o áudio dos dois vídeos...",
                                             "es": "Extrayendo el audio de ambos videos..."},
    "Measuring loudness and silence...": {"ko": "음량과 무음 측정 중...", "pt": "Medindo volume e silêncio...",
                                          "es": "Midiendo volumen y silencio..."},
    "Transcribing the original speech...": {"ko": "원본 음성 받아쓰는 중...", "pt": "Transcrevendo a fala original...",
                                            "es": "Transcribiendo el habla original..."},
    "Transcribing the dubbed speech...": {"ko": "더빙 음성 받아쓰는 중...", "pt": "Transcrevendo a fala dublada...",
                                          "es": "Transcribiendo el habla doblada..."},
    "Analyzing lip movement in the dubbed video...": {"ko": "더빙 영상의 입 움직임 분석 중...",
                                                      "pt": "Analisando o movimento dos lábios no vídeo dublado...",
                                                      "es": "Analizando el movimiento de los labios en el video doblado..."},
    "Analyzing lip movement in the original video...": {"ko": "원본 영상의 입 움직임 분석 중...",
                                                        "pt": "Analisando o movimento dos lábios no vídeo original...",
                                                        "es": "Analizando el movimiento de los labios en el video original..."},
    "Done": {"ko": "완료", "pt": "Pronto", "es": "Listo"},
}


def t(key: str, lang: str, /, **values) -> str:
    """The text for key in lang (English if that translation is missing), with {placeholders} filled in."""
    entry = TEXT[key]
    text = entry.get(lang) or entry[DEFAULT_UI_LANGUAGE]
    return text.format(**values) if values else text


def translate_message(message: str, lang: str) -> str:
    """Translates a fixed progress message from src/; anything unknown is returned unchanged."""
    return (MESSAGES.get(message) or {}).get(lang, message)


def pick_ui_language(locale: Optional[str]) -> str:
    """The interface language for a browser locale such as ko-KR or pt-BR; English if it isn't one of ours."""
    code = (locale or "").split("-")[0].lower()
    return code if code in UI_LANGUAGES else DEFAULT_UI_LANGUAGE
