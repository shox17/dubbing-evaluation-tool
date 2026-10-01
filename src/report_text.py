"""Every sentence of the quality report in English, Korean, Portuguese (Brazil) and Spanish.

Keys start with "r."; src/i18n.py merges them into TEXT, so tests/test_i18n.py checks that every entry has all four
languages with the same {placeholders}. Counted texts come in _one / _many pairs (see report._pl).
"""

REPORT_TEXT = {
    # ----- measure names -----
    "r.m.length_match": {"en": "Length match", "ko": "길이 일치", "pt": "Duração", "es": "Duración"},
    "r.m.loudness_match": {"en": "Loudness match", "ko": "음량 일치", "pt": "Volume", "es": "Volumen"},
    "r.m.silence": {"en": "Silence", "ko": "무음", "pt": "Silêncio", "es": "Silencio"},
    "r.m.clipping": {"en": "Distortion", "ko": "소리 왜곡", "pt": "Distorção", "es": "Distorsión"},
    "r.m.speech_rate": {"en": "Speaking pace", "ko": "말 속도", "pt": "Ritmo da fala", "es": "Ritmo del habla"},
    "r.m.language": {"en": "Dub language", "ko": "더빙 언어", "pt": "Idioma da dublagem", "es": "Idioma del doblaje"},
    "r.m.clarity": {"en": "Voice clarity", "ko": "음성 명료도", "pt": "Clareza da voz", "es": "Claridad de la voz"},
    "r.m.script_accuracy": {"en": "Matches your script", "ko": "내 스크립트 일치", "pt": "Fidelidade ao seu roteiro",
                            "es": "Coincide con tu guion"},
    "r.m.speech_overlap": {"en": "Speech timing", "ko": "발화 타이밍", "pt": "Momento da fala", "es": "Momento del habla"},
    "r.m.speech_offsets": {"en": "Start and end of speech", "ko": "말의 시작과 끝", "pt": "Início e fim da fala",
                           "es": "Inicio y fin del habla"},
    "r.m.translation_check": {"en": "Translation check", "ko": "번역 검토", "pt": "Verificação da tradução",
                              "es": "Revisión de la traducción"},
    "r.m.meaning": {"en": "Meaning preserved", "ko": "의미 보존", "pt": "Sentido preservado", "es": "Sentido conservado"},
    "r.m.completeness": {"en": "Missing or added content", "ko": "누락·추가된 내용", "pt": "Conteúdo faltando ou a mais",
                         "es": "Contenido que falta o sobra"},
    "r.m.voice_quality": {"en": "Voice quality", "ko": "목소리 품질", "pt": "Qualidade da voz", "es": "Calidad de la voz"},
    "r.m.names_numbers": {"en": "Names and numbers", "ko": "이름과 숫자", "pt": "Nomes e números", "es": "Nombres y números"},
    "r.m.mistranslations": {"en": "Mistranslations", "ko": "오역", "pt": "Erros de tradução", "es": "Errores de traducción"},
    "r.m.file_check": {"en": "Video file", "ko": "영상 파일", "pt": "Arquivo de vídeo", "es": "Archivo de video"},
    "r.m.lip_movement": {"en": "Lip movement", "ko": "입 움직임", "pt": "Movimento dos lábios",
                         "es": "Movimiento de los labios"},

    # ----- length -----
    "r.length.same": {
        "en": "The dub is exactly as long as the original ({dub} s and {orig} s). Nothing is cut off at the end and no "
              "silence was added.",
        "ko": "더빙이 원본과 길이가 정확히 같습니다({dub}초, {orig}초). 끝부분이 잘리거나 무음이 추가되지 않았습니다.",
        "pt": "A dublagem tem exatamente a mesma duração do original ({dub} s e {orig} s). Nada foi cortado no final e "
              "nenhum silêncio foi adicionado.",
        "es": "El doblaje dura exactamente lo mismo que el original ({dub} s y {orig} s). No se corta nada al final ni "
              "se añadió silencio.",
    },
    "r.length.longer_ok": {
        "en": "The dub is {diff} s longer than the original ({pct}%). That is small enough that viewers won't notice.",
        "ko": "더빙이 원본보다 {diff}초 깁니다({pct}%). 시청자가 알아차리지 못할 만큼 작은 차이입니다.",
        "pt": "A dublagem é {diff} s mais longa que o original ({pct}%). A diferença é pequena demais para ser notada.",
        "es": "El doblaje dura {diff} s más que el original ({pct}%). La diferencia es tan pequeña que no se nota.",
    },
    "r.length.shorter_ok": {
        "en": "The dub is {diff} s shorter than the original ({pct}%). That is small enough that viewers won't notice.",
        "ko": "더빙이 원본보다 {diff}초 짧습니다({pct}%). 시청자가 알아차리지 못할 만큼 작은 차이입니다.",
        "pt": "A dublagem é {diff} s mais curta que o original ({pct}%). A diferença é pequena demais para ser notada.",
        "es": "El doblaje dura {diff} s menos que el original ({pct}%). La diferencia es tan pequeña que no se nota.",
    },
    "r.length.longer_bad": {
        "en": "The dub is {diff} s longer than the original ({pct}%). The end of the dubbed speech may be cut off, or the "
              "voice may run past the picture. Watch the last seconds.",
        "ko": "더빙이 원본보다 {diff}초 깁니다({pct}%). 더빙 음성의 끝이 잘리거나 화면보다 길게 이어질 수 있습니다. "
              "마지막 몇 초를 확인하세요.",
        "pt": "A dublagem é {diff} s mais longa que o original ({pct}%). O final da fala dublada pode ser cortado ou "
              "passar do vídeo. Assista aos últimos segundos.",
        "es": "El doblaje dura {diff} s más que el original ({pct}%). El final del habla doblada puede cortarse o "
              "pasar del video. Mira los últimos segundos.",
    },
    "r.length.shorter_bad": {
        "en": "The dub is {diff} s shorter than the original ({pct}%). The speech may finish early and leave silence at "
              "the end, or part of the content may be missing. Watch the last seconds.",
        "ko": "더빙이 원본보다 {diff}초 짧습니다({pct}%). 말이 일찍 끝나 끝부분에 무음이 남거나 내용 일부가 빠졌을 수 "
              "있습니다. 마지막 몇 초를 확인하세요.",
        "pt": "A dublagem é {diff} s mais curta que o original ({pct}%). A fala pode terminar antes e deixar silêncio no "
              "final, ou parte do conteúdo pode faltar. Assista aos últimos segundos.",
        "es": "El doblaje dura {diff} s menos que el original ({pct}%). El habla puede terminar antes y dejar silencio al "
              "final, o puede faltar parte del contenido. Mira los últimos segundos.",
    },
    "r.length.na": {
        "en": "The original video has no audio, so the length couldn't be compared.",
        "ko": "원본 영상에 오디오가 없어 길이를 비교할 수 없습니다.",
        "pt": "O vídeo original não tem áudio, então a duração não pôde ser comparada.",
        "es": "El video original no tiene audio, así que no se pudo comparar la duración.",
    },
    "r.g.length": {
        "en": "Good when the lengths differ by at most {good}%, Check up to {check}%, otherwise Poor.",
        "ko": "길이 차이가 {good}% 이하면 좋음, {check}% 이하면 확인 필요, 그보다 크면 미흡입니다.",
        "pt": "Bom se as durações diferem até {good}%, Verificar até {check}%, acima disso Ruim.",
        "es": "Bien si las duraciones difieren como mucho un {good}%, Revisar hasta un {check}%, si no Deficiente.",
    },

    # ----- loudness -----
    "r.loud.same": {
        "en": "The dub is as loud as the original, so viewers won't need to change the volume.",
        "ko": "더빙이 원본과 같은 음량이라 시청자가 볼륨을 바꿀 필요가 없습니다.",
        "pt": "A dublagem tem o mesmo volume do original, então o público não precisa ajustar o volume.",
        "es": "El doblaje suena igual de fuerte que el original, así que no hace falta cambiar el volumen.",
    },
    "r.loud.louder_ok": {
        "en": "The dub is slightly louder than the original ({db} dB). A difference this small is hard to hear.",
        "ko": "더빙이 원본보다 조금 큽니다({db} dB). 이 정도 차이는 귀로 거의 구분되지 않습니다.",
        "pt": "A dublagem está um pouco mais alta que o original ({db} dB). Uma diferença tão pequena quase não se ouve.",
        "es": "El doblaje suena un poco más fuerte que el original ({db} dB). Una diferencia tan pequeña casi no se oye.",
    },
    "r.loud.quieter_ok": {
        "en": "The dub is slightly quieter than the original ({db} dB). A difference this small is hard to hear.",
        "ko": "더빙이 원본보다 조금 작습니다({db} dB). 이 정도 차이는 귀로 거의 구분되지 않습니다.",
        "pt": "A dublagem está um pouco mais baixa que o original ({db} dB). Uma diferença tão pequena quase não se ouve.",
        "es": "El doblaje suena un poco más bajo que el original ({db} dB). Una diferencia tan pequeña casi no se oye.",
    },
    "r.loud.louder_bad": {
        "en": "The dub is {db} dB louder than the original. Viewers will likely notice the jump in volume and may have "
              "to turn it down.",
        "ko": "더빙이 원본보다 {db} dB 큽니다. 시청자가 소리가 커진 것을 느끼고 볼륨을 줄여야 할 수 있습니다.",
        "pt": "A dublagem está {db} dB mais alta que o original. O público provavelmente vai notar o salto de volume e "
              "precisar abaixá-lo.",
        "es": "El doblaje suena {db} dB más fuerte que el original. Es probable que se note el salto de volumen y haya "
              "que bajarlo.",
    },
    "r.loud.quieter_bad": {
        "en": "The dub is {db} dB quieter than the original. Viewers will likely notice the drop in volume and may have "
              "to turn it up.",
        "ko": "더빙이 원본보다 {db} dB 작습니다. 시청자가 소리가 작아진 것을 느끼고 볼륨을 키워야 할 수 있습니다.",
        "pt": "A dublagem está {db} dB mais baixa que o original. O público provavelmente vai notar a queda de volume e "
              "precisar aumentá-lo.",
        "es": "El doblaje suena {db} dB más bajo que el original. Es probable que se note la bajada de volumen y haya "
              "que subirlo.",
    },
    "r.loud.na": {
        "en": "The original video is silent, so the loudness couldn't be compared.",
        "ko": "원본 영상이 무음이라 음량을 비교할 수 없습니다.",
        "pt": "O vídeo original está em silêncio, então o volume não pôde ser comparado.",
        "es": "El video original está en silencio, así que no se pudo comparar el volumen.",
    },
    "r.g.loudness": {
        "en": "Good within {good} dB of the original, Check within {check} dB, otherwise Poor. About 1 dB is the "
              "smallest change most people can hear.",
        "ko": "원본과의 차이가 {good} dB 이내면 좋음, {check} dB 이내면 확인 필요, 그보다 크면 미흡입니다. 대부분의 "
              "사람은 약 1 dB부터 차이를 느낍니다.",
        "pt": "Bom até {good} dB de diferença do original, Verificar até {check} dB, acima disso Ruim. Cerca de 1 dB é a "
              "menor mudança que a maioria das pessoas percebe.",
        "es": "Bien hasta {good} dB de diferencia con el original, Revisar hasta {check} dB, si no Deficiente. Cerca de "
              "1 dB es el cambio más pequeño que la mayoría percibe.",
    },

    # ----- silence -----
    "r.silence.ok": {
        "en": "The dub has about as much silence as the original ({orig} → {dub} of the time), so there are no "
              "unexpected gaps in the voice.",
        "ko": "더빙의 무음 비율이 원본과 비슷해({orig} → {dub}) 목소리가 갑자기 끊기는 곳이 없습니다.",
        "pt": "A dublagem tem quase o mesmo silêncio que o original ({orig} → {dub} do tempo), então não há pausas "
              "inesperadas na voz.",
        "es": "El doblaje tiene casi el mismo silencio que el original ({orig} → {dub} del tiempo), así que no hay pausas "
              "inesperadas en la voz.",
    },
    "r.silence.bad": {
        "en": "The dub is silent much more often than the original ({orig} → {dub} of the time, {pts} points more). "
              "Look for places where the voice drops out.",
        "ko": "더빙이 원본보다 훨씬 자주 조용합니다({orig} → {dub}, {pts}%p 증가). 목소리가 끊기는 곳이 있는지 확인하세요.",
        "pt": "A dublagem fica em silêncio com muito mais frequência que o original ({orig} → {dub} do tempo, {pts} pontos "
              "a mais). Procure trechos em que a voz some.",
        "es": "El doblaje está en silencio mucho más a menudo que el original ({orig} → {dub} del tiempo, {pts} puntos "
              "más). Busca partes donde la voz desaparece.",
    },
    "r.g.silence": {
        "en": "Good when the dub is silent at most {good} points more of the time than the original, Check up to "
              "{check} points, otherwise Poor.",
        "ko": "더빙의 무음 비율이 원본보다 {good}%p 이하로 많으면 좋음, {check}%p 이하면 확인 필요, 그보다 크면 미흡입니다.",
        "pt": "Bom se a dublagem fica em silêncio no máximo {good} pontos a mais que o original, Verificar até {check} "
              "pontos, acima disso Ruim.",
        "es": "Bien si el doblaje está en silencio como mucho {good} puntos más que el original, Revisar hasta {check} "
              "puntos, si no Deficiente.",
    },

    # ----- clipping -----
    "r.clip.ok": {
        "en": "The dub's audio never hits the maximum level, so there is no crackling or distortion.",
        "ko": "더빙 오디오가 최대 음량 한계에 닿지 않아 지직거림이나 왜곡이 없습니다.",
        "pt": "O áudio da dublagem nunca atinge o nível máximo, então não há chiado nem distorção.",
        "es": "El audio del doblaje nunca llega al nivel máximo, así que no hay crujidos ni distorsión.",
    },
    "r.clip.bad": {
        "en": "{pct}% of the dub's audio hits the maximum level. That can sound like crackling or distortion; listen to "
              "the loud parts.",
        "ko": "더빙 오디오의 {pct}%가 최대 음량 한계에 닿습니다. 지직거리거나 찌그러진 소리로 들릴 수 있으니 큰 소리 "
              "부분을 들어 보세요.",
        "pt": "{pct}% do áudio da dublagem atinge o nível máximo. Isso pode soar como chiado ou distorção; ouça as partes "
              "mais altas.",
        "es": "El {pct}% del audio del doblaje llega al nivel máximo. Puede sonar a crujidos o distorsión; escucha las "
              "partes más fuertes.",
    },
    "r.g.clipping": {
        "en": "Good when at most {good}% of the audio hits the maximum level, Check up to {check}%, otherwise Poor.",
        "ko": "최대 음량에 닿는 비율이 {good}% 이하면 좋음, {check}% 이하면 확인 필요, 그보다 크면 미흡입니다.",
        "pt": "Bom se no máximo {good}% do áudio atinge o nível máximo, Verificar até {check}%, acima disso Ruim.",
        "es": "Bien si como mucho el {good}% del audio llega al nivel máximo, Revisar hasta el {check}%, si no Deficiente.",
    },

    # ----- speaking pace -----
    "r.pace.good": {
        "en": "The dub speaks at a natural pace ({rate}). The translation fits the time available.",
        "ko": "더빙이 자연스러운 속도로 말합니다({rate}). 번역문이 주어진 시간에 잘 맞습니다.",
        "pt": "A dublagem fala em um ritmo natural ({rate}). A tradução cabe no tempo disponível.",
        "es": "El doblaje habla a un ritmo natural ({rate}). La traducción cabe en el tiempo disponible.",
    },
    "r.pace.check": {
        "en": "The dub speaks quickly ({rate}). The translation may be a little long for the time available, so some "
              "lines may sound hurried.",
        "ko": "더빙이 빠르게 말합니다({rate}). 번역문이 주어진 시간보다 조금 길어서 일부 문장이 급하게 들릴 수 있습니다.",
        "pt": "A dublagem fala rápido ({rate}). A tradução pode estar um pouco longa para o tempo disponível, então algumas "
              "falas podem soar apressadas.",
        "es": "El doblaje habla rápido ({rate}). La traducción puede ser algo larga para el tiempo disponible, así que "
              "algunas frases pueden sonar apresuradas.",
    },
    "r.pace.poor": {
        "en": "The dub speaks very fast ({rate}). The translation is probably too long for the time available, so lines "
              "will sound rushed. A shorter translation would help.",
        "ko": "더빙이 매우 빠르게 말합니다({rate}). 번역문이 주어진 시간에 비해 너무 길어 문장이 쫓기듯 들릴 것입니다. "
              "번역을 더 짧게 하면 좋아집니다.",
        "pt": "A dublagem fala muito rápido ({rate}). A tradução provavelmente é longa demais para o tempo disponível, "
              "então as falas vão soar corridas. Uma tradução mais curta ajudaria.",
        "es": "El doblaje habla muy rápido ({rate}). La traducción probablemente es demasiado larga para el tiempo "
              "disponible, así que las frases sonarán atropelladas. Una traducción más corta ayudaría.",
    },
    "r.pace.no_rule": {
        "en": "There is no speaking-pace rule for {lang} yet, so the pace ({rate}) is not graded.",
        "ko": "아직 이 언어({lang})의 말 속도 기준이 없어 속도({rate})를 평가하지 않습니다.",
        "pt": "Ainda não há regra de ritmo de fala para {lang}, então o ritmo ({rate}) não é avaliado.",
        "es": "Todavía no hay una regla de ritmo para {lang}, así que el ritmo ({rate}) no se califica.",
    },
    "r.g.pace": {
        "en": "Good up to {good} {unit}, Check up to {check} {unit}, otherwise Poor (faster than people normally speak).",
        "ko": "{good} {unit}까지 좋음, {check} {unit}까지 확인 필요, 그보다 빠르면 미흡입니다(보통 사람이 말하는 속도보다 빠름).",
        "pt": "Bom até {good} {unit}, Verificar até {check} {unit}, acima disso Ruim (mais rápido do que se fala "
              "normalmente).",
        "es": "Bien hasta {good} {unit}, Revisar hasta {check} {unit}, si no Deficiente (más rápido de lo que se habla "
              "normalmente).",
    },
    "r.no_speech": {
        "en": "No speech was recognised in the dub, so this couldn't be measured.",
        "ko": "더빙에서 말소리가 인식되지 않아 측정할 수 없습니다.",
        "pt": "Nenhuma fala foi reconhecida na dublagem, então isso não pôde ser medido.",
        "es": "No se reconoció habla en el doblaje, así que no se pudo medir.",
    },

    # ----- dub language -----
    "r.lang.good": {
        "en": "Speech recognition hears {lang} in the dub ({prob} sure), which is the language it was dubbed into.",
        "ko": "음성 인식 결과 더빙에서 들리는 언어: {lang}(확신도 {prob}). 요청한 더빙 언어와 같습니다.",
        "pt": "O reconhecimento de fala ouve {lang} na dublagem ({prob} de certeza), que é o idioma escolhido.",
        "es": "El reconocimiento de voz oye {lang} en el doblaje ({prob} de seguridad), que es el idioma elegido.",
    },
    "r.lang.check": {
        "en": "The dub is probably in {lang}, but speech recognition is only {prob} sure. Listen to confirm the right "
              "language was used.",
        "ko": "더빙 언어가 {lang}(으)로 보이지만 음성 인식의 확신도가 {prob}뿐입니다. 올바른 언어인지 직접 들어 확인하세요.",
        "pt": "A dublagem provavelmente está em {lang}, mas o reconhecimento de fala tem só {prob} de certeza. Ouça para "
              "confirmar o idioma.",
        "es": "El doblaje probablemente está en {lang}, pero el reconocimiento de voz solo tiene un {prob} de seguridad. "
              "Escucha para confirmar el idioma.",
    },
    "r.lang.poor": {
        "en": "Speech recognition hears a different language ('{detected}') instead of {lang}. The wrong language may have "
              "been generated, or the original voice was left in.",
        "ko": "요청한 언어는 {lang}인데 음성 인식 결과 다른 언어('{detected}')가 들립니다. 잘못된 언어로 생성되었거나 원본 "
              "음성이 그대로 남아 있을 수 있습니다.",
        "pt": "O reconhecimento de fala ouve outro idioma ('{detected}') em vez de {lang}. O idioma errado pode ter sido "
              "gerado, ou a voz original ficou no vídeo.",
        "es": "El reconocimiento de voz oye otro idioma ('{detected}') en lugar de {lang}. Pudo generarse el idioma "
              "equivocado o quedar la voz original.",
    },
    "r.lang.unsupported": {
        "en": "Speech recognition can't identify {lang}, so the language couldn't be checked.",
        "ko": "음성 인식이 이 언어({lang})를 구분하지 못해 언어를 확인할 수 없습니다.",
        "pt": "O reconhecimento de fala não identifica {lang}, então o idioma não pôde ser verificado.",
        "es": "El reconocimiento de voz no identifica {lang}, así que no se pudo comprobar el idioma.",
    },
    "r.lang.display": {"en": "{lang} ({prob} sure)", "ko": "{lang} (확신도 {prob})", "pt": "{lang} ({prob} de certeza)",
                       "es": "{lang} ({prob} de seguridad)"},
    "r.g.language": {
        "en": "Good when the dub is in the requested language and speech recognition is at least {prob} sure.",
        "ko": "요청한 언어이고 음성 인식 확신도가 {prob} 이상이면 좋음입니다.",
        "pt": "Bom se a dublagem está no idioma pedido e o reconhecimento de fala tem pelo menos {prob} de certeza.",
        "es": "Bien si el doblaje está en el idioma pedido y el reconocimiento de voz tiene al menos un {prob} de "
              "seguridad.",
    },

    # ----- voice clarity -----
    "r.clarity.good": {
        "en": "Speech recognition understood {pct} of the dub without trouble, so the voice is easy to understand.",
        "ko": "음성 인식이 더빙의 {pct}를 문제없이 알아들었습니다. 목소리가 알아듣기 쉽습니다.",
        "pt": "O reconhecimento de fala entendeu {pct} da dublagem sem dificuldade, então a voz é fácil de entender.",
        "es": "El reconocimiento de voz entendió el {pct} del doblaje sin problemas, así que la voz se entiende bien.",
    },
    "r.clarity.check": {
        "en": "Speech recognition struggled with {unclear} of the dub ({n} parts). Those parts may be mumbled or unclear; "
              "they are listed under Things to check.",
        "ko": "음성 인식이 더빙의 {unclear}({n}곳)를 알아듣기 어려워했습니다. 발음이 뭉개졌거나 불분명할 수 있으며, "
              "확인할 사항에 목록이 있습니다.",
        "pt": "O reconhecimento de fala teve dificuldade com {unclear} da dublagem ({n} trechos). Esses trechos podem estar "
              "abafados ou pouco claros; eles aparecem em Pontos a verificar.",
        "es": "El reconocimiento de voz tuvo problemas con el {unclear} del doblaje ({n} partes). Pueden estar poco claras; "
              "aparecen en Cosas que revisar.",
    },
    "r.clarity.poor": {
        "en": "A large part of the dub ({unclear}, {n} parts) was hard to understand. Listen to the parts listed under "
              "Things to check.",
        "ko": "더빙의 상당 부분({unclear}, {n}곳)을 알아듣기 어렵습니다. 확인할 사항에 있는 부분을 들어 보세요.",
        "pt": "Grande parte da dublagem ({unclear}, {n} trechos) foi difícil de entender. Ouça os trechos em Pontos a "
              "verificar.",
        "es": "Gran parte del doblaje ({unclear}, {n} partes) fue difícil de entender. Escucha las partes de Cosas que "
              "revisar.",
    },
    "r.clarity.display": {"en": "{pct} clear", "ko": "{pct} 명료", "pt": "{pct} claro", "es": "{pct} claro"},
    "r.g.clarity": {
        "en": "Good when at least {good}% of the speech is understood clearly, Check from {check}%, otherwise Poor.",
        "ko": "말소리의 {good}% 이상을 또렷하게 알아들으면 좋음, {check}% 이상이면 확인 필요, 그보다 낮으면 미흡입니다.",
        "pt": "Bom se pelo menos {good}% da fala é entendida com clareza, Verificar a partir de {check}%, abaixo disso Ruim.",
        "es": "Bien si al menos el {good}% del habla se entiende con claridad, Revisar desde el {check}%, si no Deficiente.",
    },
    "r.script": {
        "en": "{acc} of your script was heard in the dub. A different but correct wording also lowers this score.",
        "ko": "스크립트의 {acc}가 더빙에서 들렸습니다. 표현이 다르지만 올바른 번역도 점수를 낮춥니다.",
        "pt": "{acc} do seu roteiro foi ouvido na dublagem. Uma redação diferente, mas correta, também baixa esta nota.",
        "es": "Se oyó el {acc} de tu guion en el doblaje. Una redacción distinta pero correcta también baja esta nota.",
    },
    "r.g.script": {
        "en": "Good from {good}%, Check from {check}%, otherwise Poor.",
        "ko": "{good}% 이상이면 좋음, {check}% 이상이면 확인 필요, 그보다 낮으면 미흡입니다.",
        "pt": "Bom a partir de {good}%, Verificar a partir de {check}%, abaixo disso Ruim.",
        "es": "Bien desde el {good}%, Revisar desde el {check}%, si no Deficiente.",
    },

    # ----- speech timing -----
    "r.align.good": {
        "en": "The dub speaks at the same moments as the original ({ov} of the speaking time lines up), so the voice "
              "matches when the speaker talks on screen.",
        "ko": "더빙이 원본과 같은 순간에 말합니다(말하는 시간의 {ov}가 일치). 화면 속 화자가 말할 때 목소리가 맞게 "
              "나옵니다.",
        "pt": "A dublagem fala nos mesmos momentos que o original ({ov} do tempo de fala coincide), então a voz combina "
              "com quando a pessoa fala na tela.",
        "es": "El doblaje habla en los mismos momentos que el original (coincide el {ov} del tiempo de habla), así que la "
              "voz encaja con cuando la persona habla en pantalla.",
    },
    "r.align.check": {
        "en": "The dub mostly speaks at the same moments as the original ({ov} lines up), but some parts are off.",
        "ko": "더빙이 대체로 원본과 같은 순간에 말하지만({ov} 일치) 어긋나는 부분이 있습니다.",
        "pt": "A dublagem fala quase sempre nos mesmos momentos que o original ({ov} coincide), mas alguns trechos "
              "estão fora.",
        "es": "El doblaje habla casi siempre en los mismos momentos que el original (coincide el {ov}), pero algunas "
              "partes no.",
    },
    "r.align.poor": {
        "en": "The dub often speaks when the original is silent, or stays silent when the original speaks (only {ov} "
              "lines up). The voice won't match the picture in those places.",
        "ko": "원본이 조용할 때 더빙이 말하거나 원본이 말할 때 더빙이 조용한 경우가 많습니다({ov}만 일치). 그 부분에서는 "
              "목소리가 화면과 맞지 않습니다.",
        "pt": "A dublagem muitas vezes fala quando o original está em silêncio, ou fica calada quando o original fala "
              "(só {ov} coincide). Nesses trechos a voz não combina com a imagem.",
        "es": "El doblaje a menudo habla cuando el original calla, o calla cuando el original habla (solo coincide el "
              "{ov}). En esas partes la voz no encaja con la imagen.",
    },
    "r.align.na": {
        "en": "Speech wasn't found in one of the videos, so the timing couldn't be compared.",
        "ko": "한쪽 영상에서 말소리를 찾지 못해 타이밍을 비교할 수 없습니다.",
        "pt": "Não foi encontrada fala em um dos vídeos, então o tempo não pôde ser comparado.",
        "es": "No se encontró habla en uno de los videos, así que no se pudo comparar el momento.",
    },
    "r.align.spots_one": {
        "en": "{n} short moment doesn't line up; it is listed under Things to check.",
        "ko": "짧게 어긋나는 곳이 {n}곳 있으며 확인할 사항에 나와 있습니다.",
        "pt": "{n} momento curto não coincide; ele aparece em Pontos a verificar.",
        "es": "{n} momento corto no coincide; aparece en Cosas que revisar.",
    },
    "r.align.spots_many": {
        "en": "{n} short moments don't line up; they are listed under Things to check.",
        "ko": "짧게 어긋나는 곳이 {n}곳 있으며 확인할 사항에 나와 있습니다.",
        "pt": "{n} momentos curtos não coincidem; eles aparecem em Pontos a verificar.",
        "es": "{n} momentos cortos no coinciden; aparecen en Cosas que revisar.",
    },
    "r.align.display": {"en": "{ov} lined up", "ko": "{ov} 일치", "pt": "{ov} coincide", "es": "{ov} coincide"},
    "r.g.align": {
        "en": "Good when at least {good}% of the speaking time lines up, Check from {check}%, otherwise Poor. Languages "
              "have different rhythms, so 100% isn't expected.",
        "ko": "말하는 시간의 {good}% 이상이 일치하면 좋음, {check}% 이상이면 확인 필요, 그보다 낮으면 미흡입니다. 언어마다 "
              "리듬이 달라 100%는 기대하지 않습니다.",
        "pt": "Bom se pelo menos {good}% do tempo de fala coincide, Verificar a partir de {check}%, abaixo disso Ruim. Cada "
              "idioma tem seu ritmo, então 100% não é esperado.",
        "es": "Bien si coincide al menos el {good}% del tiempo de habla, Revisar desde el {check}%, si no Deficiente. Cada "
              "idioma tiene su ritmo, así que no se espera un 100%.",
    },
    "r.offsets": {
        "en": "The dub starts speaking {start} s {start_way} and stops {end} s {end_way} than the original. Shown for "
              "information; it doesn't change the verdict.",
        "ko": "더빙은 원본보다 {start}초 {start_way} 말하기 시작해 {end}초 {end_way} 끝납니다. 참고용이며 판정에는 영향이 "
              "없습니다.",
        "pt": "A dublagem começa a falar {start} s {start_way} e termina {end} s {end_way} que o original. É só "
              "informação; não muda o resultado.",
        "es": "El doblaje empieza a hablar {start} s {start_way} y termina {end} s {end_way} que el original. Es solo "
              "informativo; no cambia el resultado.",
    },
    "r.later": {"en": "later", "ko": "늦게", "pt": "depois", "es": "más tarde"},
    "r.earlier": {"en": "earlier", "ko": "일찍", "pt": "antes", "es": "antes"},

    # ----- translation -----
    "r.meaning.good": {
        "en": "The meaning comes across correctly.", "ko": "의미가 올바르게 전달됩니다.",
        "pt": "O sentido é transmitido corretamente.", "es": "El sentido se transmite correctamente.",
    },
    "r.meaning.check": {
        "en": "Some meaning is lost or changed; read the issues below.",
        "ko": "일부 의미가 빠지거나 달라졌습니다. 아래 문제를 확인하세요.",
        "pt": "Parte do sentido se perdeu ou mudou; leia os problemas abaixo.",
        "es": "Parte del sentido se pierde o cambia; lee los problemas de abajo.",
    },
    "r.meaning.poor": {
        "en": "The dub often says something different from the original; the translation needs to be redone.",
        "ko": "더빙이 원본과 다른 내용을 말하는 경우가 많습니다. 번역을 다시 해야 합니다.",
        "pt": "A dublagem muitas vezes diz algo diferente do original; a tradução precisa ser refeita.",
        "es": "El doblaje a menudo dice algo distinto del original; hay que rehacer la traducción.",
    },
    "r.g.meaning": {
        "en": "Rated 1–5 by {model} from both transcripts: Good from {good}, Check at {check}, otherwise Poor.",
        "ko": "두 받아쓰기를 비교해 1–5점으로 평가(평가 모델: {model}): {good}점 이상 좋음, {check}점 확인 필요, 그보다 낮으면 미흡.",
        "pt": "Nota de 1 a 5 dada por {model} com base nas duas transcrições: Bom a partir de {good}, Verificar em {check}, "
              "abaixo disso Ruim.",
        "es": "Nota de 1 a 5 de {model} a partir de las dos transcripciones: Bien desde {good}, Revisar en {check}, si no "
              "Deficiente.",
    },
    "r.issues.none_completeness": {
        "en": "Nothing important from the original is missing, and nothing was added.",
        "ko": "원본의 중요한 내용이 빠지지 않았고 추가된 내용도 없습니다.",
        "pt": "Nada importante do original está faltando, e nada foi acrescentado.",
        "es": "No falta nada importante del original y no se añadió nada.",
    },
    "r.issues.none_names_numbers": {
        "en": "Names and numbers are kept correctly.", "ko": "이름과 숫자가 올바르게 유지되었습니다.",
        "pt": "Nomes e números foram mantidos corretamente.", "es": "Los nombres y números se mantienen correctamente.",
    },
    "r.issues.none_mistranslations": {
        "en": "No passage changes the meaning.", "ko": "의미가 바뀐 부분이 없습니다.",
        "pt": "Nenhum trecho muda o sentido.", "es": "Ningún pasaje cambia el sentido.",
    },
    "r.issues.found_one": {
        "en": "{n} problem found ({major} serious). It is listed under Things to check with the original and dubbed words.",
        "ko": "문제 {n}건을 찾았습니다(심각 {major}건). 원본과 더빙 문장과 함께 확인할 사항에 나와 있습니다.",
        "pt": "{n} problema encontrado ({major} grave). Ele aparece em Pontos a verificar com as palavras originais e "
              "dubladas.",
        "es": "{n} problema encontrado ({major} grave). Aparece en Cosas que revisar con las palabras originales y dobladas.",
    },
    "r.issues.found_many": {
        "en": "{n} problems found ({major} serious). They are listed under Things to check with the original and dubbed "
              "words.",
        "ko": "문제 {n}건을 찾았습니다(심각 {major}건). 원본과 더빙 문장과 함께 확인할 사항에 나와 있습니다.",
        "pt": "{n} problemas encontrados ({major} graves). Eles aparecem em Pontos a verificar com as palavras originais e "
              "dubladas.",
        "es": "{n} problemas encontrados ({major} graves). Aparecen en Cosas que revisar con las palabras originales y "
              "dobladas.",
    },
    "r.issues.maybe_only_one": {
        "en": "{n} possible mistake, but it is probably a speech-recognition error, not a dubbing error, so it doesn't "
              "lower the grade. Listen to it under Things to check.",
        "ko": "문제로 보이는 곳이 {n}곳 있지만 더빙 오류가 아니라 음성 인식 오류일 가능성이 높아 등급을 낮추지 않습니다. "
              "확인할 사항에서 직접 들어 보세요.",
        "pt": "{n} possível erro, mas provavelmente é um erro do reconhecimento de fala, não da dublagem, então não baixa "
              "a nota. Ouça em Pontos a verificar.",
        "es": "{n} posible error, pero probablemente es del reconocimiento de voz, no del doblaje, así que no baja la nota. "
              "Escúchalo en Cosas que revisar.",
    },
    "r.issues.maybe_only_many": {
        "en": "{n} possible mistakes, but they are probably speech-recognition errors, not dubbing errors, so they don't "
              "lower the grade. Listen to them under Things to check.",
        "ko": "문제로 보이는 곳이 {n}곳 있지만 더빙 오류가 아니라 음성 인식 오류일 가능성이 높아 등급을 낮추지 않습니다. "
              "확인할 사항에서 직접 들어 보세요.",
        "pt": "{n} possíveis erros, mas provavelmente são do reconhecimento de fala, não da dublagem, então não baixam a "
              "nota. Ouça em Pontos a verificar.",
        "es": "{n} posibles errores, pero probablemente son del reconocimiento de voz, no del doblaje, así que no bajan la "
              "nota. Escúchalos en Cosas que revisar.",
    },
    "r.issues.plus_maybe_one": {
        "en": "{n} more is probably a speech-recognition error and doesn't count.",
        "ko": "그 밖의 {n}건은 음성 인식 오류로 보여 계산하지 않습니다.",
        "pt": "Mais {n} provavelmente é erro do reconhecimento de fala e não conta.",
        "es": "{n} más probablemente es un error del reconocimiento de voz y no cuenta.",
    },
    "r.issues.plus_maybe_many": {
        "en": "{n} more are probably speech-recognition errors and don't count.",
        "ko": "그 밖의 {n}건은 음성 인식 오류로 보여 계산하지 않습니다.",
        "pt": "Mais {n} provavelmente são erros do reconhecimento de fala e não contam.",
        "es": "{n} más probablemente son errores del reconocimiento de voz y no cuentan.",
    },
    "r.issues.count_one": {"en": "{n} problem", "ko": "문제 {n}건", "pt": "{n} problema", "es": "{n} problema"},
    "r.issues.count_many": {"en": "{n} problems", "ko": "문제 {n}건", "pt": "{n} problemas", "es": "{n} problemas"},
    "r.issues.maybe_count_one": {"en": "{n} possible mishearing", "ko": "인식 오류 추정 {n}건",
                                 "pt": "{n} possível erro de escuta", "es": "{n} posible error de escucha"},
    "r.issues.maybe_count_many": {"en": "{n} possible mishearings", "ko": "인식 오류 추정 {n}건",
                                  "pt": "{n} possíveis erros de escuta", "es": "{n} posibles errores de escucha"},
    "r.g.issues": {
        "en": "Good with no problems, Check with minor ones only, Poor with any serious one. Probable speech-recognition "
              "errors don't count.",
        "ko": "문제가 없으면 좋음, 사소한 문제만 있으면 확인 필요, 심각한 문제가 하나라도 있으면 미흡입니다. 음성 인식 "
              "오류로 보이는 것은 계산하지 않습니다.",
        "pt": "Bom sem problemas, Verificar só com problemas leves, Ruim com qualquer problema grave. Prováveis erros do "
              "reconhecimento de fala não contam.",
        "es": "Bien sin problemas, Revisar solo con problemas leves, Deficiente con cualquier problema grave. Los "
              "probables errores del reconocimiento de voz no cuentan.",
    },
    "r.judge.off": {
        "en": "The translation check was turned off for this run.",
        "ko": "이번 실행에서는 번역 검토를 끄고 진행했습니다.",
        "pt": "A verificação da tradução foi desligada nesta execução.",
        "es": "La revisión de la traducción se desactivó en esta ejecución.",
    },
    "r.judge.no_speech": {
        "en": "One of the videos has no recognised speech, so there was nothing to compare.",
        "ko": "한쪽 영상에서 말소리가 인식되지 않아 비교할 내용이 없습니다.",
        "pt": "Um dos vídeos não tem fala reconhecida, então não havia o que comparar.",
        "es": "Uno de los videos no tiene habla reconocida, así que no había nada que comparar.",
    },
    "r.judge.no_key": {
        "en": "The translation check needs an API key. Add GEMINI_API_KEY to the .env file and run again.",
        "ko": "번역 검토에는 API 키가 필요합니다. .env 파일에 GEMINI_API_KEY를 추가하고 다시 실행하세요.",
        "pt": "A verificação da tradução precisa de uma chave de API. Adicione GEMINI_API_KEY ao arquivo .env e execute "
              "de novo.",
        "es": "La revisión de la traducción necesita una clave de API. Añade GEMINI_API_KEY al archivo .env y vuelve a "
              "ejecutar.",
    },
    "r.judge.bad_key": {
        "en": "{model} rejected the API key. Check the key in the .env file and run again.",
        "ko": "{model} 서비스가 API 키를 거부했습니다. .env 파일의 키를 확인하고 다시 실행하세요.",
        "pt": "O {model} recusou a chave de API. Confira a chave no arquivo .env e execute de novo.",
        "es": "{model} rechazó la clave de API. Revisa la clave en el archivo .env y vuelve a ejecutar.",
    },
    "r.judge.busy": {
        "en": "{model} is busy right now (it was tried several times). Run the evaluation again in a minute; the other "
              "results are not affected.",
        "ko": "{model} 서비스가 지금 혼잡합니다(여러 번 시도함). 1분 뒤 다시 평가해 보세요. 다른 결과에는 영향이 없습니다.",
        "pt": "O {model} está ocupado agora (foram feitas várias tentativas). Rode a avaliação de novo em um minuto; os "
              "outros resultados não são afetados.",
        "es": "{model} está ocupado ahora (se intentó varias veces). Vuelve a evaluar en un minuto; los demás resultados "
              "no se ven afectados.",
    },
    "r.judge.unreachable": {
        "en": "{model} couldn't be reached. Check the internet connection and run again; the other results are not "
              "affected.",
        "ko": "{model} 서비스에 연결할 수 없습니다. 인터넷 연결을 확인하고 다시 실행하세요. 다른 결과에는 영향이 없습니다.",
        "pt": "Não foi possível acessar o {model}. Confira a conexão com a internet e execute de novo; os outros "
              "resultados não são afetados.",
        "es": "No se pudo contactar con {model}. Revisa la conexión a internet y vuelve a ejecutar; los demás resultados "
              "no se ven afectados.",
    },
    "r.judge.error": {
        "en": "{model} returned an error, so the translation wasn't checked. The other results are not affected.",
        "ko": "{model} 서비스에서 오류가 발생해 번역을 검토하지 못했습니다. 다른 결과에는 영향이 없습니다.",
        "pt": "O {model} retornou um erro, então a tradução não foi verificada. Os outros resultados não são afetados.",
        "es": "{model} devolvió un error, así que no se revisó la traducción. Los demás resultados no se ven afectados.",
    },
    "r.judge.declined": {
        "en": "{model} declined to review this content, so the translation wasn't checked.",
        "ko": "{model} 서비스가 이 내용의 검토를 거절해 번역을 확인하지 못했습니다.",
        "pt": "O {model} se recusou a revisar este conteúdo, então a tradução não foi verificada.",
        "es": "{model} se negó a revisar este contenido, así que no se revisó la traducción.",
    },
    "r.judge.cut_off": {
        "en": "{model}'s review was cut off before it finished, so the translation wasn't checked.",
        "ko": "{model}의 검토가 끝나기 전에 끊겨 번역을 확인하지 못했습니다.",
        "pt": "A revisão do {model} foi interrompida antes de terminar, então a tradução não foi verificada.",
        "es": "La revisión de {model} se cortó antes de terminar, así que no se revisó la traducción.",
    },
    "r.judge.unreadable": {
        "en": "{model}'s review couldn't be read, so the translation wasn't checked.",
        "ko": "{model}의 검토 결과를 읽을 수 없어 번역을 확인하지 못했습니다.",
        "pt": "Não foi possível ler a revisão do {model}, então a tradução não foi verificada.",
        "es": "No se pudo leer la revisión de {model}, así que no se revisó la traducción.",
    },

    # ----- video file -----
    "r.file.ok": {
        "en": "The dub keeps the original picture ({res}, {fps} fps) and has an audio track, so only the voice was changed.",
        "ko": "더빙 영상이 원본 화면({res}, {fps} fps)을 그대로 유지하고 오디오 트랙도 있습니다. 목소리만 바뀌었습니다.",
        "pt": "A dublagem mantém a imagem original ({res}, {fps} fps) e tem faixa de áudio, então só a voz mudou.",
        "es": "El doblaje mantiene la imagen original ({res}, {fps} fps) y tiene pista de audio, así que solo cambió la voz.",
    },
    "r.file.unreadable": {
        "en": "The dubbed file can't be read; it may be damaged.", "ko": "더빙 파일을 읽을 수 없습니다. 손상되었을 수 있습니다.",
        "pt": "O arquivo dublado não pode ser lido; ele pode estar danificado.",
        "es": "El archivo doblado no se puede leer; puede estar dañado.",
    },
    "r.file.no_audio": {
        "en": "The dubbed file has no audio track, so viewers would hear nothing.",
        "ko": "더빙 파일에 오디오 트랙이 없어 시청자에게 아무 소리도 들리지 않습니다.",
        "pt": "O arquivo dublado não tem faixa de áudio, então o público não ouviria nada.",
        "es": "El archivo doblado no tiene pista de audio, así que no se oiría nada.",
    },
    "r.file.resolution": {
        "en": "The picture size changed from {orig} to {dub}.", "ko": "화면 크기가 {orig}에서 {dub}로 바뀌었습니다.",
        "pt": "O tamanho da imagem mudou de {orig} para {dub}.", "es": "El tamaño de la imagen cambió de {orig} a {dub}.",
    },
    "r.file.fps": {
        "en": "The frame rate changed from {orig} to {dub} fps, which can make motion look different.",
        "ko": "프레임 속도가 {orig}에서 {dub} fps로 바뀌어 움직임이 달라 보일 수 있습니다.",
        "pt": "A taxa de quadros mudou de {orig} para {dub} fps, o que pode deixar o movimento diferente.",
        "es": "La velocidad de fotogramas cambió de {orig} a {dub} fps, lo que puede hacer que el movimiento se vea distinto.",
    },
    "r.file.na": {
        "en": "The video files weren't inspected in this run.", "ko": "이번 실행에서는 영상 파일을 점검하지 않았습니다.",
        "pt": "Os arquivos de vídeo não foram inspecionados nesta execução.",
        "es": "Los archivos de video no se revisaron en esta ejecución.",
    },
    "r.file.audio_yes": {"en": "audio ✓", "ko": "오디오 ✓", "pt": "áudio ✓", "es": "audio ✓"},
    "r.file.audio_no": {"en": "no audio", "ko": "오디오 없음", "pt": "sem áudio", "es": "sin audio"},
    "r.g.file": {
        "en": "Good when the picture size and frame rate match the original and there is an audio track.",
        "ko": "화면 크기와 프레임 속도가 원본과 같고 오디오 트랙이 있으면 좋음입니다.",
        "pt": "Bom se o tamanho da imagem e a taxa de quadros são iguais aos do original e há faixa de áudio.",
        "es": "Bien si el tamaño de la imagen y la velocidad de fotogramas coinciden con el original y hay pista de audio.",
    },

    # ----- lip movement -----
    "r.lips.info": {
        "en": "Mouth movement and voice line up with a score of {r}; the original video scores {orig}. Compare the two: "
              "a score close to or above the original's is better. This is an experimental hint, not a grade.",
        "ko": "입 움직임과 목소리의 일치 점수는 {r}이고, 원본 영상은 {orig}입니다. 두 값을 비교하세요. 원본에 가깝거나 "
              "더 높으면 좋습니다. 실험적인 참고 지표이며 등급이 아닙니다.",
        "pt": "O movimento da boca e a voz combinam com nota {r}; o vídeo original tem {orig}. Compare os dois: uma nota "
              "próxima ou acima da do original é melhor. É uma indicação experimental, não uma nota final.",
        "es": "El movimiento de la boca y la voz coinciden con una nota de {r}; el video original tiene {orig}. Compara las "
              "dos: una nota cercana o superior a la del original es mejor. Es una pista experimental, no una nota.",
    },
    "r.lips.display": {"en": "score {r}", "ko": "점수 {r}", "pt": "nota {r}", "es": "nota {r}"},
    "r.lips.not_lipsynced": {
        "en": "This dub isn't lip-synced, so there are no re-drawn lips to check.",
        "ko": "립싱크 영상이 아니라 다시 그려진 입 모양이 없어 확인할 것이 없습니다.",
        "pt": "Esta dublagem não tem sincronização labial, então não há lábios refeitos para verificar.",
        "es": "Este doblaje no tiene sincronización labial, así que no hay labios regenerados que revisar.",
    },
    "r.lips.skipped": {
        "en": "Lip movement was skipped for this run.", "ko": "이번 실행에서는 입 움직임 측정을 건너뛰었습니다.",
        "pt": "O movimento dos lábios foi pulado nesta execução.",
        "es": "El movimiento de los labios se omitió en esta ejecución.",
    },
    "r.lips.failed": {
        "en": "Lip movement couldn't be measured: {reason}", "ko": "입 움직임을 측정할 수 없습니다: {reason}",
        "pt": "Não foi possível medir o movimento dos lábios: {reason}",
        "es": "No se pudo medir el movimiento de los labios: {reason}",
    },
    "r.lips.no_video": {
        "en": "the video couldn't be opened.", "ko": "영상을 열 수 없습니다.",
        "pt": "o vídeo não pôde ser aberto.", "es": "no se pudo abrir el video.",
    },
    "r.lips.few_frames": {
        "en": "the video is too short (only {n} frames).", "ko": "영상이 너무 짧습니다({n}프레임).",
        "pt": "o vídeo é curto demais (só {n} quadros).", "es": "el video es demasiado corto (solo {n} fotogramas).",
    },
    "r.lips.few_faces": {
        "en": "a face is visible in only {pct} of the video.", "ko": "영상의 {pct}에서만 얼굴이 보입니다.",
        "pt": "um rosto aparece em só {pct} do vídeo.", "es": "solo se ve una cara en el {pct} del video.",
    },
    "r.lips.no_motion": {
        "en": "the mouth never moves.", "ko": "입이 움직이지 않습니다.",
        "pt": "a boca nunca se mexe.", "es": "la boca nunca se mueve.",
    },

    # ----- things to check -----
    "r.cat.timing": {"en": "timing", "ko": "타이밍", "pt": "tempo", "es": "momento"},
    "r.cat.clarity": {"en": "clarity", "ko": "명료도", "pt": "clareza", "es": "claridad"},
    "r.cat.missing": {"en": "missing speech", "ko": "누락된 말", "pt": "fala faltando", "es": "habla que falta"},
    "r.cat.added": {"en": "added speech", "ko": "추가된 말", "pt": "fala acrescentada", "es": "habla añadida"},
    "r.cat.long_silence": {"en": "long silence", "ko": "긴 무음", "pt": "silêncio longo", "es": "silencio largo"},
    "r.cat.distortion": {"en": "distortion", "ko": "소리 찌그러짐", "pt": "distorção", "es": "distorsión"},
    "r.cat.loudness_jump": {"en": "loudness jump", "ko": "음량 급변", "pt": "salto de volume", "es": "salto de volumen"},
    "r.cat.wrong_language": {"en": "wrong language", "ko": "다른 언어", "pt": "idioma errado", "es": "idioma incorrecto"},
    "r.cat.mistranslation": {"en": "mistranslation", "ko": "오역", "pt": "erro de tradução", "es": "error de traducción"},
    "r.cat.name_or_number": {"en": "name or number", "ko": "이름·숫자", "pt": "nome ou número", "es": "nombre o número"},
    "r.cat.general": {"en": "general", "ko": "일반", "pt": "geral", "es": "general"},
    "r.todo.dub_only": {
        "en": "The dub speaks here, but the original is silent. The voice may not match the picture.",
        "ko": "원본은 조용한데 더빙이 말하고 있습니다. 목소리가 화면과 맞지 않을 수 있습니다.",
        "pt": "A dublagem fala aqui, mas o original está em silêncio. A voz pode não combinar com a imagem.",
        "es": "El doblaje habla aquí, pero el original calla. La voz puede no encajar con la imagen.",
    },
    "r.todo.original_only": {
        "en": "The original speaks here, but the dub is silent. A line may be missing from the dub.",
        "ko": "원본은 말하는데 더빙이 조용합니다. 더빙에서 문장이 빠졌을 수 있습니다.",
        "pt": "O original fala aqui, mas a dublagem está em silêncio. Pode faltar uma fala na dublagem.",
        "es": "El original habla aquí, pero el doblaje calla. Puede faltar una frase en el doblaje.",
    },
    "r.todo.unclear": {
        "en": "This part of the dub is hard to understand: “{text}”. Listen to check the voice is clear.",
        "ko": "더빙의 이 부분을 알아듣기 어렵습니다: “{text}”. 목소리가 또렷한지 들어 보세요.",
        "pt": "Este trecho da dublagem é difícil de entender: “{text}”. Ouça para ver se a voz está clara.",
        "es": "Esta parte del doblaje se entiende mal: “{text}”. Escucha para comprobar que la voz es clara.",
    },
    "r.cat.voice_quality": {"en": "voice quality", "ko": "목소리 품질", "pt": "qualidade da voz", "es": "calidad de la voz"},
    "r.int.voice_quality": {
        "en": "Around here the dub's voice sounds clearly worse than the original's (score {dub} against {orig}): "
              "listen for a robotic, distorted or muffled voice.",
        "ko": "이 부근에서 더빙 목소리가 원본보다 확실히 나쁘게 들립니다(점수 {dub}, 원본 {orig}). 기계음, 찌그러짐, "
              "먹먹한 소리가 나는지 들어 보세요.",
        "pt": "Por aqui a voz da dublagem soa claramente pior que a do original (nota {dub} contra {orig}): ouça se a voz "
              "está robótica, distorcida ou abafada.",
        "es": "Por aquí la voz del doblaje suena claramente peor que la del original (nota {dub} frente a {orig}): "
              "escucha si suena robótica, distorsionada o apagada.",
    },
    "r.vq.good": {
        "en": "The dub's voice sounds as clean as the original's where both speak (score {dub} against {orig} on a 1-5 "
              "scale). No robotic or distorted sound stands out.",
        "ko": "두 트랙이 함께 말하는 구간에서 더빙 목소리가 원본만큼 깨끗하게 들립니다(1~5점 중 더빙 {dub}, 원본 {orig}). "
              "기계음이나 찌그러짐이 눈에 띄지 않습니다.",
        "pt": "A voz da dublagem soa tão limpa quanto a do original onde os dois falam (nota {dub} contra {orig}, de 1 a "
              "5). Nenhum som robótico ou distorcido se destaca.",
        "es": "La voz del doblaje suena tan limpia como la del original donde hablan los dos (nota {dub} frente a "
              "{orig}, de 1 a 5). No destaca ningún sonido robótico ni distorsionado.",
    },
    "r.vq.check_one": {
        "en": "In {n} of {total} stretches the dub's voice sounds a little worse than the original's at the same moment. "
              "Listen there for a slightly robotic or distorted voice.",
        "ko": "{total}개 구간 중 {n}개에서 더빙 목소리가 같은 순간의 원본보다 조금 나쁘게 들립니다. 그 부분이 약간 "
              "기계적이거나 찌그러지게 들리는지 확인하세요.",
        "pt": "Em {n} de {total} trechos a voz da dublagem soa um pouco pior que a do original no mesmo momento. Ouça "
              "ali se a voz está um pouco robótica ou distorcida.",
        "es": "En {n} de {total} tramos la voz del doblaje suena algo peor que la del original en el mismo momento. "
              "Escucha ahí si suena algo robótica o distorsionada.",
    },
    "r.vq.check_many": {
        "en": "In {n} of {total} stretches the dub's voice sounds a little worse than the original's at the same "
              "moment. Listen there for a slightly robotic or distorted voice.",
        "ko": "{total}개 구간 중 {n}개에서 더빙 목소리가 같은 순간의 원본보다 조금 나쁘게 들립니다. 그 부분들이 약간 "
              "기계적이거나 찌그러지게 들리는지 확인하세요.",
        "pt": "Em {n} de {total} trechos a voz da dublagem soa um pouco pior que a do original no mesmo momento. Ouça "
              "ali se a voz está um pouco robótica ou distorcida.",
        "es": "En {n} de {total} tramos la voz del doblaje suena algo peor que la del original en el mismo momento. "
              "Escucha ahí si suena algo robótica o distorsionada.",
    },
    "r.vq.poor_one": {
        "en": "In {n} of {total} stretches the dub's voice sounds clearly worse than the original's: viewers will likely "
              "hear a robotic or distorted voice there. Check the voice settings or regenerate that part.",
        "ko": "{total}개 구간 중 {n}개에서 더빙 목소리가 원본보다 확실히 나쁘게 들려 시청자가 기계음이나 찌그러진 소리를 "
              "들을 가능성이 높습니다. 음성 설정을 확인하거나 그 부분을 다시 생성하세요.",
        "pt": "Em {n} de {total} trechos a voz da dublagem soa claramente pior que a do original: o público "
              "provavelmente ouvirá uma voz robótica ou distorcida ali. Revise a voz ou gere essa parte de novo.",
        "es": "En {n} de {total} tramos la voz del doblaje suena claramente peor que la del original: es probable que "
              "el público oiga ahí una voz robótica o distorsionada. Revisa la voz o vuelve a generar esa parte.",
    },
    "r.vq.poor_many": {
        "en": "In {n} of {total} stretches the dub's voice sounds clearly worse than the original's: viewers will likely "
              "hear a robotic or distorted voice there. Check the voice settings or regenerate those parts.",
        "ko": "{total}개 구간 중 {n}개에서 더빙 목소리가 원본보다 확실히 나쁘게 들려 시청자가 기계음이나 찌그러진 소리를 "
              "들을 가능성이 높습니다. 음성 설정을 확인하거나 그 부분들을 다시 생성하세요.",
        "pt": "Em {n} de {total} trechos a voz da dublagem soa claramente pior que a do original: o público "
              "provavelmente ouvirá uma voz robótica ou distorcida ali. Revise a voz ou gere essas partes de novo.",
        "es": "En {n} de {total} tramos la voz del doblaje suena claramente peor que la del original: es probable que "
              "el público oiga ahí una voz robótica o distorsionada. Revisa la voz o vuelve a generar esas partes.",
    },
    "r.g.vq": {
        "en": "A voice-quality model trained on listener scores rates both tracks at the same moments (about 9 s each), "
              "where both speak, on a 1-5 scale for the voice and for the whole sound. A stretch is Check when the "
              "dub's voice scores {sig} or more below the original's or the whole sound {ovr} or more below, Poor from "
              "{sig_poor} / {ovr_poor}. The worst stretch sets the level. A muffled voice is not detected.",
        "ko": "청취자 평가로 학습한 목소리 품질 모델이 두 트랙이 함께 말하는 같은 순간(약 9초씩)을 목소리와 전체 소리에 "
              "대해 1~5점으로 평가합니다. 더빙 목소리 점수가 원본보다 {sig}점 이상 또는 전체 소리 점수가 {ovr}점 이상 "
              "낮으면 확인 필요, {sig_poor} / {ovr_poor}점 이상이면 미흡입니다. 가장 나쁜 구간이 등급을 정합니다. "
              "먹먹한 목소리는 감지하지 못합니다.",
        "pt": "Um modelo de qualidade de voz treinado com notas de ouvintes avalia as duas faixas nos mesmos momentos "
              "(cerca de 9 s cada), onde as duas falam, de 1 a 5 para a voz e para o som todo. Um trecho é Verificar "
              "quando a voz da dublagem fica {sig} ou mais abaixo da original ou o som todo {ovr} ou mais abaixo, Ruim "
              "a partir de {sig_poor} / {ovr_poor}. O pior trecho define o nível. Uma voz abafada não é detectada.",
        "es": "Un modelo de calidad de voz entrenado con notas de oyentes califica las dos pistas en los mismos momentos "
              "(unos 9 s cada uno), donde hablan las dos, de 1 a 5 para la voz y para todo el sonido. Un tramo es "
              "Revisar cuando la voz del doblaje queda {sig} o más por debajo de la original o todo el sonido {ovr} o "
              "más, Deficiente desde {sig_poor} / {ovr_poor}. El peor tramo fija el nivel. Una voz apagada no se "
              "detecta.",
    },
    "r.vq.no_common_speech": {
        "en": "The original and the dub don't speak at the same time long enough to compare their voices.",
        "ko": "원본과 더빙이 동시에 말하는 시간이 짧아 목소리를 비교할 수 없습니다.",
        "pt": "O original e a dublagem não falam ao mesmo tempo por tempo suficiente para comparar as vozes.",
        "es": "El original y el doblaje no hablan a la vez el tiempo suficiente para comparar sus voces.",
    },
    "r.vq.too_noisy": {
        "en": "The original's voice itself scores low ({orig} of 5, usually because of loud music or noise), so it "
              "can't serve as a reference for the dub's voice quality.",
        "ko": "원본 목소리 점수 자체가 낮아(5점 중 {orig}, 보통 큰 음악이나 소음 때문) 더빙 목소리 품질의 기준으로 쓸 수 "
              "없습니다.",
        "pt": "A própria voz do original tem nota baixa ({orig} de 5, em geral por música alta ou ruído), então não serve "
              "de referência para a qualidade da voz da dublagem.",
        "es": "La propia voz del original tiene nota baja ({orig} de 5, normalmente por música fuerte o ruido), así que "
              "no sirve de referencia para la calidad de la voz del doblaje.",
    },
    "r.vq.error": {
        "en": "The voice-quality model couldn't run on this machine, so voice quality wasn't measured.",
        "ko": "이 컴퓨터에서 목소리 품질 모델을 실행하지 못해 목소리 품질을 측정하지 않았습니다.",
        "pt": "O modelo de qualidade de voz não pôde rodar nesta máquina, então a qualidade da voz não foi medida.",
        "es": "El modelo de calidad de voz no pudo ejecutarse en este equipo, así que no se midió la calidad de la voz.",
    },
    "r.vq.old": {
        "en": "This result was made before voice quality was measured. Run the evaluation again to get it.",
        "ko": "목소리 품질 측정이 추가되기 전에 만든 결과입니다. 다시 평가하면 볼 수 있습니다.",
        "pt": "Este resultado foi gerado antes da medição da qualidade da voz. Avalie de novo para obtê-la.",
        "es": "Este resultado se hizo antes de que se midiera la calidad de la voz. Vuelve a evaluar para obtenerla.",
    },
    "r.int.long_silence": {
        "en": "The original speaks for {sec} s here, but the dub is silent. A line is probably missing from the dub.",
        "ko": "원본은 여기서 {sec}초 동안 말하는데 더빙은 조용합니다. 더빙에서 문장이 빠졌을 가능성이 높습니다.",
        "pt": "O original fala por {sec} s aqui, mas a dublagem fica em silêncio. Provavelmente falta uma fala.",
        "es": "El original habla {sec} s aquí, pero el doblaje calla. Probablemente falta una frase en el doblaje.",
    },
    "r.int.clipping": {
        "en": "The dub's audio hits the maximum level here and distorts. Listen for crackling.",
        "ko": "여기서 더빙 소리가 최대 음량을 넘어 찌그러집니다. 지직거리는 소리가 나는지 들어 보세요.",
        "pt": "O áudio da dublagem atinge o nível máximo aqui e distorce. Ouça se há chiado.",
        "es": "El audio del doblaje llega al nivel máximo aquí y se distorsiona. Escucha si hay chasquidos.",
    },
    "r.int.louder": {
        "en": "The dub is about {db} dB louder than the original here. Listen for a sudden jump in volume.",
        "ko": "여기서 더빙이 원본보다 약 {db} dB 더 큽니다. 음량이 갑자기 커지는지 들어 보세요.",
        "pt": "A dublagem está cerca de {db} dB mais alta que o original aqui. Ouça se o volume salta de repente.",
        "es": "El doblaje suena unos {db} dB más fuerte que el original aquí. Escucha si el volumen salta de golpe.",
    },
    "r.int.quieter": {
        "en": "The dub is about {db} dB quieter than the original here. Viewers may struggle to hear this part.",
        "ko": "여기서 더빙이 원본보다 약 {db} dB 더 작습니다. 시청자가 이 부분을 잘 듣지 못할 수 있습니다.",
        "pt": "A dublagem está cerca de {db} dB mais baixa que o original aqui. Pode ser difícil ouvir este trecho.",
        "es": "El doblaje suena unos {db} dB más bajo que el original aquí. Puede costar oír esta parte.",
    },
    "r.int.original_language": {
        "en": "This part sounds like {lang}, the original language. The original voice may have been left in, or "
              "the line wasn't dubbed.",
        "ko": "이 부분은 원본 언어({lang})처럼 들립니다. 원래 목소리가 남아 있거나 이 문장이 더빙되지 않았을 수 있습니다.",
        "pt": "Este trecho soa como {lang}, o idioma original. A voz original pode ter ficado, ou a fala não foi dublada.",
        "es": "Esta parte suena a {lang}, el idioma original. Puede que quedara la voz original o que la frase no se "
              "doblara.",
    },
    "r.int.other_language": {
        "en": "This part sounds like {detected}, not {expected}. Check that it was dubbed into the right language.",
        "ko": "이 부분은 기대한 언어({expected})가 아니라 다른 언어({detected})처럼 들립니다. 올바른 언어로 더빙됐는지 "
              "확인하세요.",
        "pt": "Este trecho soa como {detected}, não {expected}. Confira se foi dublado no idioma certo.",
        "es": "Esta parte suena a {detected}, no a {expected}. Comprueba que se dobló al idioma correcto.",
    },
    "r.todo.maybe_asr": {
        "en": "(Probably a speech-recognition error, not a dubbing error.)",
        "ko": "(더빙 오류가 아니라 음성 인식 오류일 가능성이 높습니다.)",
        "pt": "(Provavelmente um erro do reconhecimento de fala, não da dublagem.)",
        "es": "(Probablemente un error del reconocimiento de voz, no del doblaje.)",
    },
    "r.warn.length": {
        "en": "The dub ({dub} s) and the original ({orig} s) differ in length by more than 20%; they may not be the same "
              "video.",
        "ko": "더빙({dub}초)과 원본({orig}초)의 길이가 20% 넘게 다릅니다. 같은 영상이 아닐 수 있습니다.",
        "pt": "A dublagem ({dub} s) e o original ({orig} s) diferem em mais de 20% na duração; talvez não sejam o mesmo "
              "vídeo.",
        "es": "El doblaje ({dub} s) y el original ({orig} s) difieren en más de un 20% de duración; puede que no sean el "
              "mismo video.",
    },
    "r.warn.no_speech": {
        "en": "Speech recognition found no speech in the dub. Check that the dub has a voice.",
        "ko": "음성 인식이 더빙에서 말소리를 찾지 못했습니다. 더빙에 목소리가 있는지 확인하세요.",
        "pt": "O reconhecimento de fala não encontrou fala na dublagem. Confira se a dublagem tem voz.",
        "es": "El reconocimiento de voz no encontró habla en el doblaje. Comprueba que el doblaje tiene voz.",
    },
    "r.warn.script": {
        "en": "Very little of the script was heard. Check that the script belongs to this video and is in the dub's "
              "language.",
        "ko": "스크립트 내용이 거의 들리지 않습니다. 스크립트가 이 영상의 것이고 더빙 언어로 되어 있는지 확인하세요.",
        "pt": "Quase nada do roteiro foi ouvido. Confira se o roteiro é deste vídeo e está no idioma da dublagem.",
        "es": "Apenas se oyó el guion. Comprueba que el guion es de este video y está en el idioma del doblaje.",
    },
    "r.warn.lips": {
        "en": "Lip movement couldn't be measured on the dubbed video.",
        "ko": "더빙 영상에서 입 움직임을 측정할 수 없었습니다.",
        "pt": "Não foi possível medir o movimento dos lábios no vídeo dublado.",
        "es": "No se pudo medir el movimiento de los labios en el video doblado.",
    },
    "r.warn.no_whisper": {
        "en": "Speech recognition doesn't know this language ({lang}), so it guessed; treat the speech results as rough.",
        "ko": "음성 인식이 이 언어({lang})를 지원하지 않아 추측했습니다. 음성 관련 결과는 대략적인 값으로 보세요.",
        "pt": "O reconhecimento de fala não conhece este idioma ({lang}), então fez uma estimativa; considere os "
              "resultados de fala aproximados.",
        "es": "El reconocimiento de voz no conoce este idioma ({lang}), así que estimó; toma los resultados de habla como "
              "aproximados.",
    },

    # ----- verdict -----
    "r.headline.good": {
        "en": "The dub passed every automatic check. A quick watch-through is still a good idea before publishing.",
        "ko": "더빙이 모든 자동 검사를 통과했습니다. 게시 전에 한 번 훑어보는 것을 권합니다.",
        "pt": "A dublagem passou em todas as verificações automáticas. Ainda vale assistir rapidamente antes de publicar.",
        "es": "El doblaje pasó todas las comprobaciones automáticas. Aun así, conviene verlo rápido antes de publicar.",
    },
    "r.headline.check_one": {
        "en": "The dub looks mostly fine. {n} item needs a quick human check; see the details and Things to check.",
        "ko": "더빙이 대체로 괜찮습니다. {n}개 항목은 사람이 잠깐 확인해야 합니다. 세부 내용과 확인할 사항을 보세요.",
        "pt": "A dublagem parece boa no geral. {n} item precisa de uma conferência rápida; veja os detalhes e os Pontos a "
              "verificar.",
        "es": "El doblaje se ve bien en general. {n} elemento necesita una revisión rápida; mira los detalles y Cosas que "
              "revisar.",
    },
    "r.headline.check_many": {
        "en": "The dub looks mostly fine. {n} items need a quick human check; see the details and Things to check.",
        "ko": "더빙이 대체로 괜찮습니다. {n}개 항목은 사람이 잠깐 확인해야 합니다. 세부 내용과 확인할 사항을 보세요.",
        "pt": "A dublagem parece boa no geral. {n} itens precisam de uma conferência rápida; veja os detalhes e os Pontos a "
              "verificar.",
        "es": "El doblaje se ve bien en general. {n} elementos necesitan una revisión rápida; mira los detalles y Cosas que "
              "revisar.",
    },
    "r.headline.poor_one": {
        "en": "The dub has {n} serious problem that should be fixed before publishing.",
        "ko": "더빙에 게시 전에 고쳐야 할 심각한 문제가 {n}개 있습니다.",
        "pt": "A dublagem tem {n} problema grave que deve ser corrigido antes de publicar.",
        "es": "El doblaje tiene {n} problema grave que conviene corregir antes de publicar.",
    },
    "r.headline.poor_many": {
        "en": "The dub has {n} serious problems that should be fixed before publishing.",
        "ko": "더빙에 게시 전에 고쳐야 할 심각한 문제가 {n}개 있습니다.",
        "pt": "A dublagem tem {n} problemas graves que devem ser corrigidos antes de publicar.",
        "es": "El doblaje tiene {n} problemas graves que conviene corregir antes de publicar.",
    },
    "r.headline.plus_check_one": {
        "en": "{n} more item needs a quick check.", "ko": "그 밖에 {n}개 항목도 확인이 필요합니다.",
        "pt": "Mais {n} item precisa de conferência.", "es": "{n} elemento más necesita revisión.",
    },
    "r.headline.plus_check_many": {
        "en": "{n} more items need a quick check.", "ko": "그 밖에 {n}개 항목도 확인이 필요합니다.",
        "pt": "Mais {n} itens precisam de conferência.", "es": "{n} elementos más necesitan revisión.",
    },
    "r.note.translation": {
        "en": "The translation is judged from the speech-recognition transcripts of both videos, so a misheard word can "
              "look like a translation mistake. Such cases are marked as probable recognition errors.",
        "ko": "번역은 두 영상의 음성 인식 받아쓰기를 바탕으로 평가하므로, 잘못 들린 단어가 번역 오류처럼 보일 수 있습니다. "
              "그런 경우는 음성 인식 오류로 표시합니다.",
        "pt": "A tradução é avaliada a partir das transcrições dos dois vídeos, então uma palavra mal ouvida pode parecer "
              "erro de tradução. Esses casos são marcados como prováveis erros de reconhecimento.",
        "es": "La traducción se evalúa con las transcripciones de ambos videos, así que una palabra mal oída puede parecer "
              "un error de traducción. Esos casos se marcan como probables errores de reconocimiento.",
    },
    "r.note.lipsync": {
        "en": "This measure is experimental: it is shown to help you look, but it never changes the overall verdict.",
        "ko": "이 항목은 실험적인 지표로, 확인에 참고하도록 보여 주지만 전체 판정에는 영향을 주지 않습니다.",
        "pt": "Esta medida é experimental: aparece para ajudar na conferência, mas nunca muda o resultado geral.",
        "es": "Esta medida es experimental: se muestra para ayudarte a revisar, pero nunca cambia el resultado general.",
    },
    "r.evaluated.lipsync": {"en": "lip-synced video", "ko": "립싱크 영상", "pt": "vídeo com sincronização labial",
                            "es": "video con sincronización labial"},
    "r.evaluated.dub": {"en": "dubbed video", "ko": "더빙 영상", "pt": "vídeo dublado", "es": "video doblado"},

    # ----- report labels (text and HTML versions) -----
    "r.label.title": {"en": "Dubbing QA Report", "ko": "더빙 품질 보고서", "pt": "Relatório de qualidade da dublagem",
                      "es": "Informe de calidad del doblaje"},
    "r.label.overall": {"en": "Overall", "ko": "종합 판정", "pt": "Resultado", "es": "Resultado"},
    "r.label.things": {"en": "Things to check", "ko": "확인할 사항", "pt": "Pontos a verificar", "es": "Cosas que revisar"},
    "r.label.nothing": {"en": "Nothing specific to check.", "ko": "특별히 확인할 곳이 없습니다.",
                        "pt": "Nada específico para verificar.", "es": "Nada específico que revisar."},
    "r.label.not_measured": {"en": "Not measured", "ko": "측정하지 않은 항목", "pt": "Não medido", "es": "No medido"},
    "r.label.method": {"en": "Method", "ko": "방법", "pt": "Método", "es": "Método"},
    "r.label.judged_by": {"en": "translation judged by", "ko": "번역 평가:", "pt": "tradução avaliada por",
                          "es": "traducción evaluada por"},
    "r.label.project": {"en": "Project", "ko": "프로젝트", "pt": "Projeto", "es": "Proyecto"},
    "r.label.languages": {"en": "Languages", "ko": "언어", "pt": "Idiomas", "es": "Idiomas"},
    "r.label.length": {"en": "Length", "ko": "길이", "pt": "Duração", "es": "Duración"},
    "r.label.evaluated": {"en": "Evaluated", "ko": "평가 대상", "pt": "Avaliado", "es": "Evaluado"},
    "r.label.source": {"en": "Source", "ko": "출처", "pt": "Origem", "es": "Origen"},
    "r.label.original": {"en": "Original", "ko": "원본", "pt": "Original", "es": "Original"},
    "r.label.dub": {"en": "Dub", "ko": "더빙", "pt": "Dublagem", "es": "Doblaje"},
    "r.label.evidence": {"en": "Transcripts of both videos", "ko": "두 영상의 받아쓰기", "pt": "Transcrições dos dois vídeos",
                         "es": "Transcripciones de ambos videos"},
    "r.label.note": {"en": "Note", "ko": "참고", "pt": "Nota", "es": "Nota"},
    "r.label.generated": {"en": "Generated by Dubbing QA Studio.", "ko": "Dubbing QA Studio에서 생성했습니다.",
                          "pt": "Gerado pelo Dubbing QA Studio.", "es": "Generado por Dubbing QA Studio."},

    # ----- compare mode (src/compare.py) -----
    "c.title": {"en": "Dub comparison", "ko": "더빙 비교", "pt": "Comparação de dublagens", "es": "Comparación de doblajes"},
    "c.sec.recommended": {"en": "Recommended version", "ko": "추천 버전", "pt": "Versão recomendada",
                          "es": "Versión recomendada"},
    "c.sec.intervals": {"en": "Problem intervals", "ko": "문제 구간", "pt": "Trechos com problemas",
                        "es": "Tramos con problemas"},
    "c.sec.reasoning": {"en": "Reasoning", "ko": "판단 근거", "pt": "Justificativa", "es": "Razonamiento"},
    "c.sec.table": {"en": "Every check, side by side", "ko": "전체 항목 나란히 보기", "pt": "Todas as verificações lado a lado",
                    "es": "Todas las comprobaciones, lado a lado"},
    "c.sec.links": {"en": "The two links", "ko": "두 링크 정보", "pt": "Os dois links", "es": "Los dos enlaces"},
    "c.sec.notes": {"en": "Measurement notes", "ko": "측정 참고 사항", "pt": "Notas sobre a medição",
                    "es": "Notas de medición"},
    "c.dub": {"en": "Dub {d}", "ko": "더빙 {d}", "pt": "Dublagem {d}", "es": "Doblaje {d}"},
    "c.recommend": {"en": "Deliver Dub {d}.", "ko": "더빙 {d} 버전을 납품하세요.", "pt": "Entregue a Dublagem {d}.",
                    "es": "Entrega el Doblaje {d}."},
    "c.recommend_tie": {
        "en": "Deliver Dub A. The two dubs are tied on every rule.",
        "ko": "더빙 A 버전을 납품하세요. 두 더빙은 모든 규칙에서 동점입니다.",
        "pt": "Entregue a Dublagem A. As duas dublagens empatam em todas as regras.",
        "es": "Entrega el Doblaje A. Los dos doblajes empatan en todas las reglas.",
    },
    "c.not_ready": {
        "en": "Neither dub is ready to deliver: both have a Poor verdict. Dub {d} is the better starting point.",
        "ko": "두 더빙 모두 납품할 준비가 되지 않았습니다(둘 다 미흡 판정). 그래도 더빙 {d} 버전에서 시작하는 편이 낫습니다.",
        "pt": "Nenhuma dublagem está pronta para entrega: as duas têm resultado Ruim. A Dublagem {d} é o melhor ponto "
              "de partida.",
        "es": "Ningún doblaje está listo para entregar: los dos tienen resultado Deficiente. El Doblaje {d} es el mejor "
              "punto de partida.",
    },
    "c.fix_first": {"en": "Fix first", "ko": "먼저 고칠 것", "pt": "Corrija primeiro", "es": "Corrige primero"},
    "c.verdict": {"en": "Verdict", "ko": "판정", "pt": "Resultado", "es": "Resultado"},
    "c.intervals_count_one": {"en": "{n} problem interval, {sec} s in total", "ko": "문제 구간 {n}개, 총 {sec}초",
                              "pt": "{n} trecho com problema, {sec} s no total",
                              "es": "{n} tramo con problemas, {sec} s en total"},
    "c.intervals_count_many": {"en": "{n} problem intervals, {sec} s in total", "ko": "문제 구간 {n}개, 총 {sec}초",
                               "pt": "{n} trechos com problemas, {sec} s no total",
                               "es": "{n} tramos con problemas, {sec} s en total"},
    "c.no_intervals": {"en": "No problem intervals.", "ko": "문제 구간이 없습니다.", "pt": "Nenhum trecho com problema.",
                       "es": "Ningún tramo con problemas."},
    "c.asr": {"en": "Possible ASR errors (listed, not counted)", "ko": "음성 인식 오류 가능성(표시만 하고 집계하지 않음)",
              "pt": "Possíveis erros de reconhecimento de fala (listados, não contados)",
              "es": "Posibles errores del reconocimiento de voz (listados, no contados)"},
    "c.rule_label": {"en": "Deciding rule", "ko": "결정 규칙", "pt": "Regra decisiva", "es": "Regla decisiva"},
    "c.values_label": {"en": "Values", "ko": "값", "pt": "Valores", "es": "Valores"},
    "c.summary_label": {"en": "Summary", "ko": "요약", "pt": "Resumo", "es": "Resumen"},
    "c.skipped": {"en": "Rules skipped (a value is missing for one dub)", "ko": "건너뛴 규칙(한쪽 더빙에 값이 없음)",
                  "pt": "Regras ignoradas (falta um valor para uma dublagem)",
                  "es": "Reglas omitidas (falta un valor para un doblaje)"},
    "c.rule.verdict": {"en": "1. Better overall verdict", "ko": "1. 더 좋은 전체 판정", "pt": "1. Melhor resultado geral",
                       "es": "1. Mejor resultado general"},
    "c.rule.poor_items": {"en": "2. Fewer Poor items", "ko": "2. 더 적은 미흡 항목", "pt": "2. Menos itens Ruins",
                          "es": "2. Menos elementos Deficientes"},
    "c.rule.check_items": {"en": "3. Fewer Check items", "ko": "3. 더 적은 확인 필요 항목", "pt": "3. Menos itens a Verificar",
                           "es": "3. Menos elementos a Revisar"},
    "c.rule.problem_seconds": {"en": "4. Less total time in problem intervals", "ko": "4. 문제 구간의 총 시간이 더 짧음",
                               "pt": "4. Menos tempo total em trechos com problemas",
                               "es": "4. Menos tiempo total en tramos con problemas"},
    "c.rule.meaning_score": {"en": "5. Higher translation meaning score", "ko": "5. 더 높은 번역 의미 점수",
                             "pt": "5. Maior nota de sentido da tradução", "es": "5. Mayor nota de sentido de la traducción"},
    "c.rule.speech_timing": {"en": "6. Higher speech-timing alignment", "ko": "6. 더 높은 발화 타이밍 일치도",
                             "pt": "6. Maior alinhamento do tempo de fala", "es": "6. Mayor alineación del momento del habla"},
    "c.rule.tie": {"en": "Tie: no rule separates the two dubs", "ko": "동점: 어떤 규칙으로도 두 더빙이 갈리지 않음",
                   "pt": "Empate: nenhuma regra separa as duas dublagens",
                   "es": "Empate: ninguna regla separa los dos doblajes"},
    "c.why.verdict": {
        "en": "Dub {win} has the better overall verdict ({win_value}; Dub {lose}: {lose_value}).",
        "ko": "더빙 {win} 쪽 전체 판정이 더 좋습니다({win_value}, 더빙 {lose}: {lose_value}).",
        "pt": "A Dublagem {win} tem o melhor resultado geral ({win_value}; Dublagem {lose}: {lose_value}).",
        "es": "El Doblaje {win} tiene el mejor resultado general ({win_value}; Doblaje {lose}: {lose_value}).",
    },
    "c.why.poor_items": {
        "en": "Both dubs have the same verdict, and Dub {win} has fewer Poor items ({win_value}; Dub {lose}: {lose_value}).",
        "ko": "두 더빙의 판정은 같지만 더빙 {win} 쪽 미흡 항목이 더 적습니다({win_value}, 더빙 {lose}: {lose_value}).",
        "pt": "As duas têm o mesmo resultado, e a Dublagem {win} tem menos itens Ruins ({win_value}; Dublagem {lose}: "
              "{lose_value}).",
        "es": "Los dos tienen el mismo resultado, y el Doblaje {win} tiene menos elementos Deficientes ({win_value}; "
              "Doblaje {lose}: {lose_value}).",
    },
    "c.why.check_items": {
        "en": "Both dubs have the same verdict and Poor items, and Dub {win} has fewer Check items ({win_value}; "
              "Dub {lose}: {lose_value}).",
        "ko": "판정과 미흡 항목 수는 같지만 더빙 {win} 쪽 확인 필요 항목이 더 적습니다({win_value}, 더빙 {lose}: "
              "{lose_value}).",
        "pt": "As duas têm o mesmo resultado e itens Ruins, e a Dublagem {win} tem menos itens a Verificar ({win_value}; "
              "Dublagem {lose}: {lose_value}).",
        "es": "Los dos tienen el mismo resultado y elementos Deficientes, y el Doblaje {win} tiene menos elementos a "
              "Revisar ({win_value}; Doblaje {lose}: {lose_value}).",
    },
    "c.why.problem_seconds": {
        "en": "Both dubs have the same verdict and item counts, and Dub {win} spends less time in problem intervals "
              "({win_value}; Dub {lose}: {lose_value}).",
        "ko": "판정과 항목 수는 같지만 더빙 {win} 쪽 문제 구간의 총 시간이 더 짧습니다({win_value}, 더빙 {lose}: "
              "{lose_value}).",
        "pt": "As duas têm o mesmo resultado e contagens, e a Dublagem {win} passa menos tempo em trechos com problemas "
              "({win_value}; Dublagem {lose}: {lose_value}).",
        "es": "Los dos tienen el mismo resultado y recuentos, y el Doblaje {win} pasa menos tiempo en tramos con "
              "problemas ({win_value}; Doblaje {lose}: {lose_value}).",
    },
    "c.why.meaning_score": {
        "en": "Both dubs are equal on verdict, items and problem time, and Dub {win} carries the original meaning "
              "better ({win_value}; Dub {lose}: {lose_value}).",
        "ko": "판정, 항목 수, 문제 시간은 같지만 더빙 {win} 쪽이 원본의 의미를 더 잘 전달합니다({win_value}, 더빙 "
              "{lose}: {lose_value}).",
        "pt": "As duas empatam em resultado, itens e tempo com problemas, e a Dublagem {win} transmite melhor o sentido "
              "original ({win_value}; Dublagem {lose}: {lose_value}).",
        "es": "Los dos empatan en resultado, elementos y tiempo con problemas, y el Doblaje {win} transmite mejor el "
              "sentido original ({win_value}; Doblaje {lose}: {lose_value}).",
    },
    "c.why.speech_timing": {
        "en": "Both dubs are equal on every earlier rule, and Dub {win} speaks more in time with the original "
              "({win_value}; Dub {lose}: {lose_value}).",
        "ko": "앞의 규칙에서는 모두 같지만 더빙 {win} 쪽이 원본과 더 같은 타이밍에 말합니다({win_value}, 더빙 {lose}: "
              "{lose_value}).",
        "pt": "As duas empatam em todas as regras anteriores, e a Dublagem {win} fala mais no tempo do original "
              "({win_value}; Dublagem {lose}: {lose_value}).",
        "es": "Los dos empatan en todas las reglas anteriores, y el Doblaje {win} habla más a tiempo con el original "
              "({win_value}; Doblaje {lose}: {lose_value}).",
    },
    "c.why.tie": {
        "en": "The two dubs are tied on all six rules, so Dub A is recommended by default.",
        "ko": "두 더빙이 여섯 가지 규칙 모두에서 동점이라 기본값으로 더빙 A 버전을 추천합니다.",
        "pt": "As duas dublagens empatam nas seis regras, então a Dublagem A é recomendada por padrão.",
        "es": "Los dos doblajes empatan en las seis reglas, así que se recomienda el Doblaje A por defecto.",
    },
    "c.loser_problems": {
        "en": "Dub {dub}'s main problems: {items}.", "ko": "더빙 {dub} 버전의 주요 문제: {items}.",
        "pt": "Principais problemas da Dublagem {dub}: {items}.", "es": "Principales problemas del Doblaje {dub}: {items}.",
    },
    "c.loser_clean": {
        "en": "Dub {dub} has no Poor or Check items; it lost only on the rule above.",
        "ko": "더빙 {dub} 버전에는 미흡이나 확인 필요 항목이 없고, 위 규칙에서만 밀렸습니다.",
        "pt": "A Dublagem {dub} não tem itens Ruins nem a Verificar; perdeu só na regra acima.",
        "es": "El Doblaje {dub} no tiene elementos Deficientes ni a Revisar; perdió solo en la regla de arriba.",
    },
    "c.ready.good": {
        "en": "Dub {dub} passed every automatic check and can be delivered.",
        "ko": "더빙 {dub} 버전은 모든 자동 검사를 통과해 납품할 수 있습니다.",
        "pt": "A Dublagem {dub} passou em todas as verificações automáticas e pode ser entregue.",
        "es": "El Doblaje {dub} pasó todas las comprobaciones automáticas y se puede entregar.",
    },
    "c.ready.check": {
        "en": "Dub {dub} can be delivered after a person reviews its Check items and problem intervals.",
        "ko": "더빙 {dub} 버전은 사람이 확인 필요 항목과 문제 구간을 검토한 뒤 납품할 수 있습니다.",
        "pt": "A Dublagem {dub} pode ser entregue depois que uma pessoa revisar os itens a Verificar e os trechos com "
              "problemas.",
        "es": "El Doblaje {dub} se puede entregar después de que una persona revise los elementos a Revisar y los "
              "tramos con problemas.",
    },
    "c.ready.poor": {
        "en": "Fix Dub {dub}'s Poor items before delivering it.",
        "ko": "납품하기 전에 더빙 {dub} 버전의 미흡 항목을 고치세요.",
        "pt": "Corrija os itens Ruins da Dublagem {dub} antes de entregá-la.",
        "es": "Corrige los elementos Deficientes del Doblaje {dub} antes de entregarlo.",
    },
    "c.translation_used": {
        "en": "The translation check ran for both dubs.", "ko": "번역 검토가 두 더빙 모두에 대해 실행됐습니다.",
        "pt": "A verificação da tradução foi feita nas duas dublagens.",
        "es": "La revisión de la traducción se hizo en los dos doblajes.",
    },
    "c.no_translation": {
        "en": "The translation check didn't run for {dubs}, so the decision was made without translation.",
        "ko": "번역 검토가 실행되지 않은 더빙이 있어({dubs}) 번역을 빼고 결정했습니다.",
        "pt": "A verificação da tradução não rodou para {dubs}, então a decisão foi tomada sem a tradução.",
        "es": "La revisión de la traducción no se hizo para {dubs}, así que la decisión se tomó sin la traducción.",
    },
    "c.rules_order": {
        "en": "Decision rule (stops at the first rule that separates the dubs): 1 better verdict, 2 fewer Poor items, "
              "3 fewer Check items, 4 less time in problem intervals, 5 higher meaning score, 6 higher speech-timing "
              "alignment; if still tied, Dub A.",
        "ko": "결정 규칙(두 더빙이 처음으로 갈리는 규칙에서 멈춤): 1 더 좋은 판정, 2 더 적은 미흡 항목, 3 더 적은 확인 필요 "
              "항목, 4 더 짧은 문제 구간 시간, 5 더 높은 의미 점수, 6 더 높은 발화 타이밍 일치도. 그래도 같으면 더빙 A.",
        "pt": "Regra de decisão (para na primeira regra que separa as dublagens): 1 melhor resultado, 2 menos itens Ruins, "
              "3 menos itens a Verificar, 4 menos tempo em trechos com problemas, 5 maior nota de sentido, 6 maior "
              "alinhamento do tempo de fala; se ainda empatar, Dublagem A.",
        "es": "Regla de decisión (se detiene en la primera regla que separa los doblajes): 1 mejor resultado, 2 menos "
              "elementos Deficientes, 3 menos elementos a Revisar, 4 menos tiempo en tramos con problemas, 5 mayor nota "
              "de sentido, 6 mayor alineación del habla; si siguen empatados, Doblaje A.",
    },
    "c.table.check": {"en": "Check", "ko": "항목", "pt": "Verificação", "es": "Comprobación"},
    "c.open_report": {"en": "Full report", "ko": "전체 보고서", "pt": "Relatório completo", "es": "Informe completo"},
    "c.meta.title": {"en": "Title", "ko": "제목", "pt": "Título", "es": "Título"},
    "c.meta.languages": {"en": "Languages", "ko": "언어", "pt": "Idiomas", "es": "Idiomas"},
    "c.meta.length": {"en": "Length", "ko": "길이", "pt": "Duração", "es": "Duración"},
    "c.meta.lipsync": {"en": "Lip-sync", "ko": "립싱크", "pt": "Sincronização labial", "es": "Sincronización labial"},
    "c.meta.project": {"en": "Perso project", "ko": "Perso 프로젝트", "pt": "Projeto Perso", "es": "Proyecto Perso"},
    "c.meta.evaluated": {"en": "Evaluated video", "ko": "평가한 영상", "pt": "Vídeo avaliado", "es": "Video evaluado"},
    "c.meta.link": {"en": "Link", "ko": "링크", "pt": "Link", "es": "Enlace"},
    "c.yes": {"en": "Yes", "ko": "예", "pt": "Sim", "es": "Sí"},
    "c.no": {"en": "No", "ko": "아니요", "pt": "Não", "es": "No"},
    "c.note.not_measured": {"en": "Dub {dub}, not measured: {items}", "ko": "더빙 {dub}, 측정하지 못한 항목: {items}",
                            "pt": "Dublagem {dub}, não medido: {items}", "es": "Doblaje {dub}, no medido: {items}"},
    "c.note.same_project": {
        "en": "Both links point to the same Perso project, so the two results describe the same dub.",
        "ko": "두 링크가 같은 Perso 프로젝트를 가리켜 두 결과가 같은 더빙에 대한 것입니다.",
        "pt": "Os dois links apontam para o mesmo projeto Perso, então os dois resultados descrevem a mesma dublagem.",
        "es": "Los dos enlaces apuntan al mismo proyecto de Perso, así que los dos resultados describen el mismo doblaje.",
    },
    "c.note.other_video": {
        "en": "The two originals differ in length ({a} s and {b} s); the links may not be dubs of the same video.",
        "ko": "두 원본의 길이가 다릅니다({a}초, {b}초). 같은 영상의 더빙이 아닐 수 있습니다.",
        "pt": "Os dois originais têm durações diferentes ({a} s e {b} s); os links podem não ser do mesmo vídeo.",
        "es": "Los dos originales duran distinto ({a} s y {b} s); puede que los enlaces no sean del mismo video.",
    },
    "c.note.other_language": {
        "en": "The two dubs are in different languages ({a} and {b}).", "ko": "두 더빙의 언어가 다릅니다({a}, {b}).",
        "pt": "As duas dublagens estão em idiomas diferentes ({a} e {b}).",
        "es": "Los dos doblajes están en idiomas distintos ({a} y {b}).",
    },
    "c.note.none": {"en": "Everything was measured for both dubs.", "ko": "두 더빙 모두 모든 항목을 측정했습니다.",
                    "pt": "Tudo foi medido nas duas dublagens.", "es": "Se midió todo en los dos doblajes."},
    "c.footer": {"en": "Dubbing QA Studio {version} · run time {sec} s · {time}",
                 "ko": "Dubbing QA Studio {version} · 실행 시간 {sec}초 · {time}",
                 "pt": "Dubbing QA Studio {version} · tempo de execução {sec} s · {time}",
                 "es": "Dubbing QA Studio {version} · tiempo de ejecución {sec} s · {time}"},

    # ----- batch mode (src/batch.py) -----
    "b.title": {"en": "Batch summary", "ko": "일괄 평가 요약", "pt": "Resumo do lote", "es": "Resumen del lote"},
    "b.counts": {"en": "{n} links: {good} Good · {check} Needs review · {poor} Poor · {failed} failed",
                 "ko": "링크 {n}개: 좋음 {good} · 검토 필요 {check} · 미흡 {poor} · 실패 {failed}",
                 "pt": "{n} links: {good} Bom · {check} Requer revisão · {poor} Ruim · {failed} com falha",
                 "es": "{n} enlaces: {good} Bien · {check} Requiere revisión · {poor} Deficiente · {failed} con error"},
    "b.failed": {"en": "could not evaluate", "ko": "평가하지 못함", "pt": "não foi possível avaliar", "es": "no se pudo evaluar"},
    "b.person": {"en": "person", "ko": "사람", "pt": "pessoa", "es": "persona"},
    "b.meaning": {"en": "meaning", "ko": "의미", "pt": "sentido", "es": "sentido"},
    "b.items": {"en": "{poor} Poor, {check} Check", "ko": "미흡 {poor}, 확인 필요 {check}", "pt": "{poor} Ruim, {check} Verificar",
                "es": "{poor} Deficiente, {check} Revisar"},
    "b.agreement": {
        "en": "Agreement with your verdicts: {agree} of {n} ({pct}%). Stricter than you: {strict}. More lenient: {lenient}.",
        "ko": "사람 판정과 일치: {n}개 중 {agree}개({pct}%). 사람보다 엄격: {strict}, 사람보다 관대: {lenient}.",
        "pt": "Concordância com seus resultados: {agree} de {n} ({pct}%). Mais rigoroso que você: {strict}. Mais "
              "brando: {lenient}.",
        "es": "Coincidencia con tus resultados: {agree} de {n} ({pct}%). Más estricto que tú: {strict}. Más "
              "permisivo: {lenient}.",
    },
    "b.person_tool": {"en": "person ↓ / tool →", "ko": "사람 ↓ / 도구 →", "pt": "pessoa ↓ / ferramenta →",
                      "es": "persona ↓ / herramienta →"},
    "b.no_labels": {
        "en": "Add your own verdict after a link (link,good / check / poor) to see how often the tool agrees with you.",
        "ko": "링크 뒤에 직접 판정을 붙이면(링크,good / check / poor) 도구가 얼마나 사람과 일치하는지 볼 수 있습니다.",
        "pt": "Adicione seu resultado depois de um link (link,good / check / poor) para ver quanto a ferramenta concorda "
              "com você.",
        "es": "Añade tu resultado después de un enlace (enlace,good / check / poor) para ver cuánto coincide la "
              "herramienta contigo.",
    },
}
