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
        "en": "Paste a Perso share link and get a detailed quality report on the dub.",
        "ko": "Perso 공유 링크를 붙여 넣으면 더빙 품질에 대한 상세 보고서를 받을 수 있습니다.",
        "pt": "Cole um link de compartilhamento da Perso e receba um relatório detalhado da dublagem.",
        "es": "Pega un enlace compartido de Perso y recibe un informe detallado del doblaje.",
    },
    "ui_language": {"en": "Interface language", "ko": "화면 언어", "pt": "Idioma da interface",
                    "es": "Idioma de la interfaz"},
    "how.title": {"en": "How it works", "ko": "작동 방식", "pt": "Como funciona", "es": "Cómo funciona"},
    "how.body": {
        "en": "1. **Paste** a Perso share link.\n"
              "2. The app **downloads** the original and the dub (the lip-synced one when there is one).\n"
              "3. Both are **measured**: length, loudness, silence, speaking pace, the dub's language and clarity "
              "(speech recognition), when each track speaks, and the video file itself.\n"
              "4. **An AI model checks the translation** (Gemini, or Claude): meaning, missing or added content, names and numbers.\n"
              "5. You get a **report**: a verdict, every measure with Good / Check / Poor and a plain explanation, "
              "and timestamped places to check.",
        "ko": "1. Perso 공유 링크를 **붙여 넣습니다**.\n"
              "2. 앱이 원본과 더빙 영상을 **다운로드**합니다(립싱크 영상이 있으면 그것을 사용).\n"
              "3. 두 영상을 **측정**합니다: 길이, 음량, 무음, 말 속도, 더빙 언어와 명료도(음성 인식), "
              "각 트랙이 말하는 구간, 영상 파일 자체.\n"
              "4. **AI 모델이 번역을 검토**합니다(Gemini 또는 Claude): 의미, 누락·추가된 내용, 이름과 숫자.\n"
              "5. **보고서**를 받습니다: 판정, 항목별 좋음 / 확인 필요 / 미흡과 쉬운 설명, 시간이 표시된 확인할 곳.",
        "pt": "1. **Cole** um link de compartilhamento da Perso.\n"
              "2. O app **baixa** o original e a dublagem (a versão com sincronização labial, se houver).\n"
              "3. Os dois são **medidos**: duração, volume, silêncio, ritmo da fala, idioma e clareza da dublagem "
              "(reconhecimento de fala), quando cada faixa fala e o próprio arquivo de vídeo.\n"
              "4. **Um modelo de IA verifica a tradução** (Gemini ou Claude): sentido, conteúdo faltando ou a mais, nomes e números.\n"
              "5. Você recebe um **relatório**: o resultado, cada medida com Bom / Verificar / Ruim e uma explicação simples, "
              "e os pontos a verificar com horário.",
        "es": "1. **Pega** un enlace compartido de Perso.\n"
              "2. La app **descarga** el original y el doblaje (el de sincronización labial, si existe).\n"
              "3. Se **miden** ambos: duración, volumen, silencio, ritmo del habla, idioma y claridad del doblaje "
              "(reconocimiento de voz), cuándo habla cada pista y el propio archivo de video.\n"
              "4. **Un modelo de IA revisa la traducción** (Gemini o Claude): sentido, contenido que falta o sobra, nombres y números.\n"
              "5. Recibes un **informe**: el resultado, cada medida con Bien / Revisar / Deficiente y una explicación sencilla, "
              "y los puntos a revisar con su momento.",
    },
    "sidebar.last_result": {"en": "Show last result", "ko": "마지막 결과 보기", "pt": "Mostrar último resultado",
                            "es": "Ver último resultado"},

    # ----- stages (progress checklist) -----
    "stage.fetch": {"en": "Read the share link", "ko": "공유 링크 읽기", "pt": "Ler o link de compartilhamento",
                    "es": "Leer el enlace compartido"},
    "stage.download": {"en": "Download both videos", "ko": "두 영상 다운로드", "pt": "Baixar os dois vídeos",
                       "es": "Descargar ambos videos"},
    "stage.evaluate": {"en": "Measure quality", "ko": "품질 측정", "pt": "Medir a qualidade", "es": "Medir la calidad"},
    "stage.dub_a": {"en": "Evaluate dub A", "ko": "더빙 A 평가", "pt": "Avaliar a dublagem A", "es": "Evaluar el doblaje A"},
    "stage.dub_b": {"en": "Evaluate dub B", "ko": "더빙 B 평가", "pt": "Avaliar a dublagem B", "es": "Evaluar el doblaje B"},
    "stage.dub_c": {"en": "Evaluate dub C", "ko": "더빙 C 평가", "pt": "Avaliar a dublagem C",
                    "es": "Evaluar el doblaje C"},
    "stage.dub_d": {"en": "Evaluate dub D", "ko": "더빙 D 평가", "pt": "Avaliar a dublagem D",
                    "es": "Evaluar el doblaje D"},
    "stage.dub_e": {"en": "Evaluate dub E", "ko": "더빙 E 평가", "pt": "Avaliar a dublagem E",
                    "es": "Evaluar el doblaje E"},
    "stage.dub_f": {"en": "Evaluate dub F", "ko": "더빙 F 평가", "pt": "Avaliar a dublagem F",
                    "es": "Evaluar el doblaje F"},
    "stage.dub_g": {"en": "Evaluate dub G", "ko": "더빙 G 평가", "pt": "Avaliar a dublagem G",
                    "es": "Evaluar el doblaje G"},
    "stage.dub_h": {"en": "Evaluate dub H", "ko": "더빙 H 평가", "pt": "Avaliar a dublagem H",
                    "es": "Evaluar el doblaje H"},
    "stage.batch": {"en": "Evaluate every link", "ko": "모든 링크 평가", "pt": "Avaliar todos os links",
                    "es": "Evaluar todos los enlaces"},
    "stage.compare": {"en": "Compare and recommend", "ko": "비교 및 추천", "pt": "Comparar e recomendar",
                      "es": "Comparar y recomendar"},

    # ----- time -----
    "time.min_sec": {"en": "{m} min {s} s", "ko": "{m}분 {s}초", "pt": "{m} min {s} s", "es": "{m} min {s} s"},
    "time.sec": {"en": "{s} s", "ko": "{s}초", "pt": "{s} s", "es": "{s} s"},

    # ----- progress page -----
    "progress.title": {"en": "Evaluating the dub", "ko": "더빙 평가 중", "pt": "Avaliando a dublagem",
                       "es": "Evaluando el doblaje"},
    "progress.title_compare": {"en": "Evaluating the dubs", "ko": "더빙 평가 중", "pt": "Avaliando as dublagens",
                               "es": "Evaluando los doblajes"},
    "progress.overall": {"en": "Overall", "ko": "전체", "pt": "Total", "es": "Total"},
    "progress.elapsed": {"en": "Elapsed", "ko": "경과 시간", "pt": "Tempo decorrido", "es": "Tiempo transcurrido"},
    "progress.stop": {"en": "Stop waiting", "ko": "기다리기 중지", "pt": "Parar de esperar", "es": "Dejar de esperar"},
    "progress.stop_help": {
        "en": "Stops this evaluation. Nothing on Perso is changed.",
        "ko": "이 평가를 중지합니다. Perso에는 아무것도 바뀌지 않습니다.",
        "pt": "Interrompe esta avaliação. Nada é alterado na Perso.",
        "es": "Detiene esta evaluación. No se cambia nada en Perso.",
    },
    "progress.stopping": {"en": "Stopping... this takes a few seconds.", "ko": "중지하는 중... 몇 초 걸립니다.",
                          "pt": "Parando... isso leva alguns segundos.", "es": "Deteniendo... tarda unos segundos."},

    # ----- results page -----
    "results.title": {"en": "Results", "ko": "결과", "pt": "Resultados", "es": "Resultados"},
    "results.download": {"en": "Data (JSON)", "ko": "데이터 (JSON)", "pt": "Dados (JSON)", "es": "Datos (JSON)"},
    "results.download_help": {"en": "The report plus every measurement as a JSON file.",
                              "ko": "보고서와 모든 측정값을 담은 JSON 파일입니다.",
                              "pt": "O relatório e todas as medições em um arquivo JSON.",
                              "es": "El informe y todas las mediciones en un archivo JSON."},
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
    "badge.good": {"en": "Good", "ko": "좋음", "pt": "Bom", "es": "Bien"},
    "badge.check": {"en": "Check", "ko": "확인 필요", "pt": "Verificar", "es": "Revisar"},
    "badge.poor": {"en": "Poor", "ko": "미흡", "pt": "Ruim", "es": "Deficiente"},
    "badge.info": {"en": "Info", "ko": "참고", "pt": "Informativo", "es": "Informativo"},
    "badge.na": {"en": "Not measured", "ko": "측정 안 함", "pt": "Não medido", "es": "No medido"},

    # ----- report (results page) -----
    "verdict.good": {"en": "Good", "ko": "좋음", "pt": "Bom", "es": "Bien"},
    "verdict.check": {"en": "Needs review", "ko": "검토 필요", "pt": "Precisa de revisão", "es": "Necesita revisión"},
    "verdict.poor": {"en": "Poor", "ko": "미흡", "pt": "Ruim", "es": "Deficiente"},
    "verdict.counts": {
        "en": "{good} good · {check} needs review · {poor} poor · {na} not measured",
        "ko": "좋음 {good} · 검토 필요 {check} · 미흡 {poor} · 측정 안 함 {na}",
        "pt": "{good} bons · {check} para revisar · {poor} ruins · {na} não medidos",
        "es": "{good} bien · {check} por revisar · {poor} deficientes · {na} sin medir",
    },
    "verdict.rule": {
        "en": "Any Poor makes the verdict Poor; otherwise any Check makes it Needs review. "
              "Info and not-measured items don't count.",
        "ko": "미흡 항목이 하나라도 있으면 '미흡', 없고 확인 필요 항목이 있으면 '검토 필요'입니다. "
              "참고와 측정 안 함 항목은 판정에 포함되지 않습니다.",
        "pt": "Qualquer item Ruim torna o resultado Ruim; senão, qualquer item Verificar o torna Precisa de revisão. "
              "Itens informativos e não medidos não contam.",
        "es": "Cualquier elemento Deficiente hace el resultado Deficiente; si no, cualquier Revisar lo hace Necesita revisión. "
              "Los informativos y los no medidos no cuentan.",
    },
    "rsec.timing_audio": {"en": "Timing & audio", "ko": "타이밍 & 오디오", "pt": "Tempo e áudio", "es": "Tiempo y audio"},
    "rsec.speech": {"en": "Speech recognition", "ko": "음성 인식", "pt": "Reconhecimento de fala",
                    "es": "Reconocimiento de voz"},
    "rsec.alignment": {"en": "Timing alignment", "ko": "발화 타이밍", "pt": "Alinhamento da fala",
                       "es": "Alineación del habla"},
    "rsec.translation": {"en": "Translation", "ko": "번역", "pt": "Tradução", "es": "Traducción"},
    "rsec.integrity": {"en": "Video integrity", "ko": "영상 무결성", "pt": "Integridade do vídeo",
                       "es": "Integridad del video"},
    "rsec.lipsync": {"en": "Lip movement (experimental)", "ko": "입 움직임 (실험적)",
                     "pt": "Movimento dos lábios (experimental)", "es": "Movimiento de los labios (experimental)"},
    "report.no_things": {"en": "Nothing specific to check.", "ko": "특별히 확인할 곳이 없습니다.",
                         "pt": "Nada específico para verificar.", "es": "Nada específico que revisar."},
    "report.jump_help": {"en": "Play both videos from this moment.", "ko": "두 영상을 이 지점부터 재생합니다.",
                         "pt": "Reproduz os dois vídeos a partir deste momento.",
                         "es": "Reproduce ambos videos desde este momento."},
    "report.not_measured": {"en": "Not measured", "ko": "측정하지 않은 항목", "pt": "Não medido", "es": "No medido"},
    "report.details": {"en": "Detailed measurements", "ko": "상세 측정값", "pt": "Medições detalhadas",
                       "es": "Mediciones detalladas"},
    "report.download_html": {"en": "Report (HTML)", "ko": "보고서 (HTML)", "pt": "Relatório (HTML)",
                             "es": "Informe (HTML)"},
    "report.download_html_help": {
        "en": "A standalone page you can open in any browser or send to your team.",
        "ko": "어느 브라우저에서나 열 수 있고 팀에 보낼 수 있는 단독 페이지입니다.",
        "pt": "Uma página independente para abrir em qualquer navegador ou enviar à equipe.",
        "es": "Una página independiente que puedes abrir en cualquier navegador o enviar a tu equipo.",
    },
    "report.timeline_title": {"en": "When each track speaks", "ko": "각 트랙이 말하는 구간", "pt": "Quando cada faixa fala",
                              "es": "Cuándo habla cada pista"},
    "report.timeline_caption": {
        "en": "Bars show speech. Red boxes mark places where only one track speaks.",
        "ko": "막대는 말하는 구간입니다. 빨간 상자는 한쪽 트랙만 말하는 곳입니다.",
        "pt": "As barras mostram a fala. Caixas vermelhas marcam trechos em que só uma faixa fala.",
        "es": "Las barras muestran el habla. Los recuadros rojos marcan donde solo habla una pista.",
    },
    "report.open_perso": {"en": "Open in Perso", "ko": "Perso에서 열기", "pt": "Abrir na Perso", "es": "Abrir en Perso"},
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
    "said.tab_dub": {"en": "Dubbed speech", "ko": "더빙 음성", "pt": "Fala dublada", "es": "Habla doblada"},
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
        "en": "Paste a Perso share link. The app compares the dub with the original and writes a report with a "
              "verdict and the places to check.",
        "ko": "Perso 공유 링크를 붙여 넣으세요. 앱이 더빙을 원본과 비교해 판정과 확인할 곳이 담긴 보고서를 만듭니다.",
        "pt": "Cole um link de compartilhamento da Perso. O app compara a dublagem com o original e gera um relatório "
              "com o resultado e os pontos a verificar.",
        "es": "Pega un enlace compartido de Perso. La app compara el doblaje con el original y genera un informe con "
              "el resultado y los puntos a revisar.",
    },
    "share.title": {"en": "① Paste a Perso share link", "ko": "① Perso 공유 링크 붙여넣기",
                    "pt": "① Cole um link de compartilhamento da Perso", "es": "① Pega un enlace compartido de Perso"},
    "share.caption": {
        "en": "Open the dubbed video in Perso, choose **Share**, and copy the link. "
              "No Perso account or credits are needed.",
        "ko": "Perso에서 더빙된 영상을 열고 **공유**를 눌러 링크를 복사하세요. Perso 계정이나 크레딧이 필요 없습니다.",
        "pt": "Abra o vídeo dublado na Perso, escolha **Compartilhar** e copie o link. "
              "Não é preciso conta nem créditos da Perso.",
        "es": "Abre el video doblado en Perso, elige **Compartir** y copia el enlace. "
              "No necesitas cuenta ni créditos de Perso.",
    },
    "share.label": {"en": "Share link", "ko": "공유 링크", "pt": "Link de compartilhamento", "es": "Enlace compartido"},
    "share.placeholder": {"en": "https://perso.ai/en/share/video-translator?seq=…",
                          "ko": "https://perso.ai/en/share/video-translator?seq=…",
                          "pt": "https://perso.ai/en/share/video-translator?seq=…",
                          "es": "https://perso.ai/en/share/video-translator?seq=…"},
    "share.info_languages": {"en": "Languages", "ko": "언어", "pt": "Idiomas", "es": "Idiomas"},
    "share.info_length": {"en": "Length", "ko": "길이", "pt": "Duração", "es": "Duración"},
    "share.info_lipsync": {"en": "Lip-sync", "ko": "립싱크", "pt": "Sincronização labial", "es": "Sincronización labial"},
    "share.info_videos": {"en": "Videos in the link", "ko": "링크에 포함된 영상", "pt": "Vídeos no link",
                          "es": "Videos en el enlace"},
    "share.info_created": {"en": "Created", "ko": "생성일", "pt": "Criado em", "es": "Creado"},
    "share.info_owner": {"en": "Owner", "ko": "소유자", "pt": "Proprietário", "es": "Propietario"},
    "share.info_project": {"en": "Perso project", "ko": "Perso 프로젝트", "pt": "Projeto Perso", "es": "Proyecto de Perso"},
    "share.yes": {"en": "Yes", "ko": "예", "pt": "Sim", "es": "Sí"},
    "share.no": {"en": "No", "ko": "아니요", "pt": "Não", "es": "No"},
    "share.video_original": {"en": "original", "ko": "원본", "pt": "original", "es": "original"},
    "share.video_dubbed": {"en": "dubbed", "ko": "더빙", "pt": "dublado", "es": "doblado"},
    "share.video_lipsync": {"en": "lip-synced", "ko": "립싱크", "pt": "com sincronização labial",
                            "es": "con sincronización labial"},
    "share.judge_missing": {
        "en": "No API key found for the translation check, so it will show as not measured. "
              "Add GEMINI_API_KEY to the .env file to turn it on.",
        "ko": "번역 검토용 API 키가 없어 '측정 안 함'으로 표시됩니다. .env 파일에 GEMINI_API_KEY를 추가하면 켜집니다.",
        "pt": "Nenhuma chave de API foi encontrada para a verificação da tradução, então ela aparecerá como não medida. "
              "Adicione GEMINI_API_KEY ao arquivo .env para ativá-la.",
        "es": "No se encontró una clave de API para la revisión de la traducción, así que aparecerá como no medida. "
              "Añade GEMINI_API_KEY al archivo .env para activarla.",
    },
    "share.start": {"en": "Evaluate this dub", "ko": "이 더빙 평가하기", "pt": "Avaliar esta dublagem",
                    "es": "Evaluar este doblaje"},
    "mode.single": {"en": "Check one dub", "ko": "더빙 하나 확인", "pt": "Verificar uma dublagem", "es": "Revisar un doblaje"},
    "mode.compare": {"en": "Compare two dubs", "ko": "더빙 두 개 비교", "pt": "Comparar duas dublagens",
                     "es": "Comparar dos doblajes"},
    "compare.title": {"en": "① Paste two Perso share links", "ko": "① Perso 공유 링크 두 개 붙여넣기",
                      "pt": "① Cole dois links de compartilhamento da Perso", "es": "① Pega dos enlaces compartidos de Perso"},
    "compare.caption": {
        "en": "Two or more dubs of the same video (for example versions, or with and without lip-sync). All are "
              "measured the same way, and the tool ranks them, recommends which one to deliver and explains why.",
        "ko": "같은 영상의 더빙을 두 개 이상 넣으세요(예: 여러 버전, 립싱크 있음/없음). 모두 같은 방식으로 측정해 순위를 "
              "매기고, 어느 쪽을 납품할지 추천하며 이유를 설명합니다.",
        "pt": "Duas ou mais dublagens do mesmo vídeo (por exemplo, versões, ou com e sem sincronização labial). Todas "
              "são medidas do mesmo jeito, e a ferramenta as classifica, recomenda qual entregar e explica por quê.",
        "es": "Dos o más doblajes del mismo video (por ejemplo, versiones, o con y sin sincronización labial). Todos se "
              "miden igual, y la herramienta los clasifica, recomienda cuál entregar y explica por qué.",
    },
    "compare.add": {"en": "Add another dub", "ko": "더빙 추가", "pt": "Adicionar outra dublagem", "es": "Añadir otro doblaje"},
    "compare.remove": {"en": "Remove the last", "ko": "마지막 더빙 빼기", "pt": "Remover a última", "es": "Quitar el último"},
    "compare.start": {"en": "Evaluate and compare", "ko": "평가하고 비교하기", "pt": "Avaliar e comparar",
                      "es": "Evaluar y comparar"},
    "compare.same_link": {
        "en": "Both links point to the same Perso project, so the comparison will show the same dub twice.",
        "ko": "두 링크가 같은 Perso 프로젝트를 가리켜 같은 더빙을 두 번 비교하게 됩니다.",
        "pt": "Os dois links apontam para o mesmo projeto Perso, então a comparação mostrará a mesma dublagem duas vezes.",
        "es": "Los dos enlaces apuntan al mismo proyecto de Perso, así que la comparación mostrará el mismo doblaje dos "
              "veces.",
    },
    "problem.compare": {"en": "Paste two valid Perso share links first.", "ko": "먼저 올바른 Perso 공유 링크 두 개를 붙여 넣으세요.",
                        "pt": "Cole primeiro dois links de compartilhamento válidos da Perso.",
                        "es": "Pega primero dos enlaces compartidos válidos de Perso."},
    "compare.download_html": {"en": "Download comparison", "ko": "비교 보고서 다운로드", "pt": "Baixar comparação",
                              "es": "Descargar comparación"},
    "compare.download_html_help": {
        "en": "One HTML file with the recommendation, problem intervals, reasoning and every check side by side.",
        "ko": "추천, 문제 구간, 판단 근거, 전체 항목 비교가 담긴 HTML 파일 하나입니다.",
        "pt": "Um arquivo HTML com a recomendação, os trechos com problemas, a justificativa e todas as verificações.",
        "es": "Un archivo HTML con la recomendación, los tramos con problemas, el razonamiento y todas las comprobaciones.",
    },
    "compare.download_json": {"en": "Download data (JSON)", "ko": "데이터 다운로드(JSON)", "pt": "Baixar dados (JSON)",
                              "es": "Descargar datos (JSON)"},
    "problem.share": {"en": "Paste a Perso share link first.", "ko": "먼저 Perso 공유 링크를 붙여 넣으세요.",
                      "pt": "Primeiro, cole um link de compartilhamento da Perso.",
                      "es": "Primero, pega un enlace compartido de Perso."},

    # ----- stopped / failed jobs -----
    "stopped.title": {"en": "Dubbing stopped", "ko": "더빙이 중지되었습니다", "pt": "Dublagem interrompida",
                      "es": "Doblaje detenido"},
    "failed.title": {"en": "Something went wrong", "ko": "문제가 발생했습니다", "pt": "Algo deu errado",
                     "es": "Algo salió mal"},
    "stopped.during": {"en": "It stopped during: {stage} · after {time}", "ko": "중지된 단계: {stage} · {time} 후",
                       "pt": "Parou durante: {stage} · depois de {time}", "es": "Se detuvo en: {stage} · tras {time}"},
    "back": {"en": "Back to setup", "ko": "설정으로 돌아가기", "pt": "Voltar à configuração",
             "es": "Volver a la configuración"},
    "untracked": {
        "en": "That evaluation is no longer being tracked (the app was restarted). Paste the share link again.",
        "ko": "앱이 다시 시작되어 해당 평가를 더 이상 추적하지 않습니다. 공유 링크를 다시 붙여 넣으세요.",
        "pt": "Essa avaliação não está mais sendo acompanhada (o app foi reiniciado). Cole o link de novo.",
        "es": "Esa evaluación ya no se está siguiendo (la app se reinició). Vuelve a pegar el enlace.",
    },
}

# Report sentences live in their own module to keep this file readable; they share t() and the tests.
from src.report_text import REPORT_TEXT  # noqa: E402

TEXT.update(REPORT_TEXT)

# Fixed English progress messages reported by src/ (Perso steps, pipeline and evaluation), translated by text.
MESSAGES = {
    # User-facing errors from src/ (share links, downloads, stopped jobs).
    'Paste a Perso share link, for example https://perso.ai/en/share/video-translator?seq=…': {"ko": 'Perso 공유 링크를 붙여 넣으세요. 예: https://perso.ai/en/share/video-translator?seq=…', "pt": 'Cole um link de compartilhamento da Perso, por exemplo https://perso.ai/en/share/video-translator?seq=…', "es": 'Pega un enlace compartido de Perso, por ejemplo https://perso.ai/en/share/video-translator?seq=…'},
    "This doesn't look like a Perso share link. Open the dubbed video in Perso, choose Share, and copy the link (it contains ?seq=).": {"ko": 'Perso 공유 링크가 아닌 것 같습니다. Perso에서 더빙 영상을 열고 공유를 눌러 링크를 복사하세요(?seq=가 포함됨).', "pt": 'Isso não parece um link de compartilhamento da Perso. Abra o vídeo dublado na Perso, escolha Compartilhar e copie o link (ele contém ?seq=).', "es": 'Esto no parece un enlace compartido de Perso. Abre el video doblado en Perso, elige Compartir y copia el enlace (contiene ?seq=).'},
    'The share link is missing its seq=… part. Copy the whole link from Perso again.': {"ko": '공유 링크에 seq=… 부분이 없습니다. Perso에서 링크 전체를 다시 복사하세요.', "pt": 'O link está sem a parte seq=…. Copie o link inteiro da Perso novamente.', "es": 'Al enlace le falta la parte seq=…. Vuelve a copiar el enlace completo desde Perso.'},
    'Sharing is turned off for this Perso project. Ask the owner to turn sharing on, then try again.': {"ko": '이 Perso 프로젝트는 공유가 꺼져 있습니다. 소유자에게 공유를 켜 달라고 요청한 뒤 다시 시도하세요.', "pt": 'O compartilhamento está desligado neste projeto da Perso. Peça ao proprietário para ativá-lo e tente de novo.', "es": 'El uso compartido está desactivado en este proyecto de Perso. Pide al propietario que lo active y vuelve a intentarlo.'},
    "Perso couldn't find a project for this share link. Check that the link is complete and that sharing is still turned on.": {"ko": 'Perso에서 이 공유 링크의 프로젝트를 찾지 못했습니다. 링크가 완전한지, 공유가 켜져 있는지 확인하세요.', "pt": 'A Perso não encontrou um projeto para este link. Confira se o link está completo e se o compartilhamento continua ativo.', "es": 'Perso no encontró un proyecto para este enlace. Comprueba que el enlace está completo y que el uso compartido sigue activo.'},
    'This shared project has no finished dubbed video yet. Wait until Perso finishes, then try again.': {"ko": '이 공유 프로젝트에는 아직 완성된 더빙 영상이 없습니다. Perso 작업이 끝난 뒤 다시 시도하세요.', "pt": 'Este projeto compartilhado ainda não tem vídeo dublado pronto. Espere a Perso terminar e tente de novo.', "es": 'Este proyecto compartido aún no tiene un video doblado terminado. Espera a que Perso termine y vuelve a intentarlo.'},
    'Perso is rate-limiting requests. Wait a minute and try again.': {"ko": 'Perso가 요청을 제한하고 있습니다. 1분 뒤 다시 시도하세요.', "pt": 'A Perso está limitando as solicitações. Espere um minuto e tente de novo.', "es": 'Perso está limitando las solicitudes. Espera un minuto y vuelve a intentarlo.'},
    'Could not reach Perso. Check your internet connection.': {"ko": 'Perso에 연결할 수 없습니다. 인터넷 연결을 확인하세요.', "pt": 'Não foi possível acessar a Perso. Confira sua conexão com a internet.', "es": 'No se pudo contactar con Perso. Revisa tu conexión a internet.'},
    'Perso request failed after retries.': {"ko": '여러 번 시도했지만 Perso 요청이 실패했습니다.', "pt": 'A solicitação à Perso falhou após várias tentativas.', "es": 'La solicitud a Perso falló tras varios intentos.'},
    'Downloading the videos from Perso failed. Try again in a minute.': {"ko": 'Perso에서 영상을 다운로드하지 못했습니다. 1분 뒤 다시 시도하세요.', "pt": 'O download dos vídeos da Perso falhou. Tente de novo em um minuto.', "es": 'No se pudieron descargar los videos de Perso. Vuelve a intentarlo en un minuto.'},
    "The shared project doesn't say which language it was dubbed into.": {"ko": '공유 프로젝트에 더빙 언어 정보가 없습니다.', "pt": 'O projeto compartilhado não informa o idioma da dublagem.', "es": 'El proyecto compartido no indica el idioma del doblaje.'},
    'You stopped this job.': {"ko": '이 작업을 중지했습니다.', "pt": 'Você interrompeu este trabalho.', "es": 'Detuviste este trabajo.'},
    "Starting...": {"ko": "시작하는 중...", "pt": "Iniciando...", "es": "Iniciando..."},
    "Finished": {"ko": "완료", "pt": "Concluído", "es": "Terminado"},
    "Downloading the dubbed video...": {"ko": "더빙된 영상 다운로드 중...", "pt": "Baixando o vídeo dublado...",
                                        "es": "Descargando el video doblado..."},
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
    "Reading the shared Perso project...": {"ko": "공유된 Perso 프로젝트 읽는 중...",
                                            "pt": "Lendo o projeto compartilhado da Perso...",
                                            "es": "Leyendo el proyecto compartido de Perso..."},
    "Downloading the original video...": {"ko": "원본 영상 다운로드 중...", "pt": "Baixando o vídeo original...",
                                          "es": "Descargando el video original..."},
    "Checking which language the dub is in...": {"ko": "더빙 언어 확인 중...", "pt": "Verificando o idioma da dublagem...",
                                                 "es": "Comprobando el idioma del doblaje..."},
    "Rating the voice quality of both tracks...": {"ko": "두 트랙의 목소리 품질 평가 중...",
                                                   "pt": "Avaliando a qualidade da voz das duas faixas...",
                                                   "es": "Calificando la calidad de la voz de ambas pistas..."},
    "Comparing the dub voice with the original speakers...": {"ko": "더빙 목소리를 원래 화자와 비교 중...",
                                                              "pt": "Comparando a voz da dublagem com os falantes originais...",
                                                              "es": "Comparando la voz del doblaje con los hablantes originales..."},
    "Comparing the dubs...": {"ko": "더빙 비교 중...", "pt": "Comparando as dublagens...",
                              "es": "Comparando los doblajes..."},
    "This share link has no original video. Pass the original with --original <file or URL> (command line), then try again.": {
        "ko": "이 공유 링크에는 원본 영상이 없습니다. 명령줄에서 --original <파일 또는 URL>로 원본을 지정한 뒤 다시 시도하세요.",
        "pt": "Este link não tem o vídeo original. Informe o original com --original <arquivo ou URL> (linha de comando) "
              "e tente de novo.",
        "es": "Este enlace no tiene el video original. Indica el original con --original <archivo o URL> (línea de "
              "comandos) y vuelve a intentarlo."},
    "Checking the dub's language part by part...": {"ko": "더빙 언어를 구간별로 확인 중...",
                                                    "pt": "Verificando o idioma da dublagem por trechos...",
                                                    "es": "Comprobando el idioma del doblaje por partes..."},
    "Comparing when each track speaks...": {"ko": "각 트랙이 말하는 구간 비교 중...",
                                            "pt": "Comparando quando cada faixa fala...",
                                            "es": "Comparando cuándo habla cada pista..."},
    "Checking the translation...": {"ko": "번역 검토 중...", "pt": "Verificando a tradução...",
                                    "es": "Revisando la traducción..."},
    "Writing the report...": {"ko": "보고서 작성 중...", "pt": "Escrevendo o relatório...", "es": "Escribiendo el informe..."},
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
