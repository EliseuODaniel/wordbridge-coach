"""Feedback payload helpers for the mock LLM provider."""

import random
from typing import Any, Dict

from app.llm.mock_text_analysis import _analyze_text


def _feedback_language_code(student_profile: Dict[str, Any]) -> str:
    return str(student_profile.get("feedback_language_code") or "en").lower()


def _microcopy(student_profile: Dict[str, Any], key: str) -> str:
    language = _feedback_language_code(student_profile)
    translations = {
        "en": {
            "spot_change": "Can you spot the word that should change before you send it?",
            "add_detail": "What extra detail could make your idea clearer?",
            "polish_form": "You already have the main idea. Now polish the form.",
            "expand_clear": "Your meaning is clear. Try one small expansion next.",
            "good_start": "Good start!",
            "almost_there": "Almost there! Check your grammar.",
            "nice_try": "Nice try!",
            "great_job": "Great job! Your sentence is well-structured.",
            "excellent_work": "Excellent work! Keep practicing.",
            "doing_great": "You're doing great!",
            "past_question": "Which word in your sentence tells the listener that the action happened in the past?",
            "detail_question": "What one extra detail could make your message more precise?",
            "retry_pattern": "You are close. Try one more sentence with the same pattern.",
            "keep_clarity": "Nice work. Keep the same clarity in your next reply.",
            "summary_past": "Good practice with past tense! Remember to use irregular verb forms correctly.",
            "summary_future": "Nice work on future forms! Keep practicing 'will' and 'going to' patterns.",
            "summary_present": "Great use of present continuous for actions happening now!",
            "summary_hobbies": "Excellent vocabulary for talking about interests and activities!",
            "summary_work": "Professional language is developing well! Keep expanding work-related vocabulary.",
            "summary_weekend": "Good use of future time expressions! Your planning vocabulary is clear.",
            "summary_start": "Great beginning! Focus on basic sentence structure and word order.",
            "summary_default": "Good effort! Keep practicing to build confidence and fluency.",
            "strength_preferences": "You used a clear sentence pattern to talk about preferences.",
            "strength_understandable": "Your main message is understandable, which is the hardest part of real conversation.",
            "strength_clear": "Your sentence communicates the idea clearly.",
            "focus_enjoy": "After verbs like 'enjoy', use the -ing form.",
            "focus_past": "Switch irregular verbs to past form when you describe past events.",
            "focus_review": "Review the main correction above and try the same pattern again in a new sentence.",
            "why_enjoy": "After 'enjoy', use the gerund (-ing form) not infinitive (to + verb)",
            "why_past": "Use past simple 'went' for past actions, not base form 'go'",
            "why_good_like": "Good sentence structure! 'I like' is correctly followed by the gerund.",
            "grammar_check": "Review your sentence structure for better clarity.",
            "verb_tense_explanation": "Use past simple with yesterday.",
            "word_choice_explanation": "Try a more natural word here.",
        },
        "pt": {
            "spot_change": "Você consegue perceber qual palavra precisa mudar antes de enviar?",
            "add_detail": "Que detalhe extra pode deixar sua ideia mais clara?",
            "polish_form": "A ideia principal já está aí. Agora ajuste a forma.",
            "expand_clear": "Sua mensagem está clara. Tente expandir com um detalhe a mais.",
            "good_start": "Bom começo!",
            "almost_there": "Quase lá! Revise a gramática.",
            "nice_try": "Boa tentativa!",
            "great_job": "Muito bem! Sua frase está bem estruturada.",
            "excellent_work": "Excelente trabalho! Continue praticando.",
            "doing_great": "Você está indo muito bem!",
            "past_question": "Qual palavra na sua frase mostra ao ouvinte que a ação aconteceu no passado?",
            "detail_question": "Que detalhe extra pode deixar sua mensagem mais precisa?",
            "retry_pattern": "Você está perto. Tente mais uma frase com o mesmo padrão.",
            "keep_clarity": "Bom trabalho. Mantenha essa clareza na próxima resposta.",
            "summary_past": "Boa prática com o passado! Lembre-se de usar corretamente os verbos irregulares.",
            "summary_future": "Bom trabalho com formas de futuro! Continue praticando os padrões com 'will' e 'going to'.",
            "summary_present": "Ótimo uso do present continuous para ações que acontecem agora!",
            "summary_hobbies": "Excelente vocabulário para falar sobre interesses e atividades!",
            "summary_work": "Sua linguagem profissional está evoluindo bem! Continue ampliando o vocabulário de trabalho.",
            "summary_weekend": "Bom uso de expressões de tempo futuro! Seu vocabulário de planejamento está claro.",
            "summary_start": "Ótimo começo! Foque na estrutura básica da frase e na ordem das palavras.",
            "summary_default": "Bom esforço! Continue praticando para ganhar confiança e fluência.",
            "strength_preferences": "Você usou um padrão de frase claro para falar sobre preferências.",
            "strength_understandable": "Sua mensagem principal é compreensível, e essa é a parte mais difícil da conversa real.",
            "strength_clear": "Sua frase comunica a ideia com clareza.",
            "focus_enjoy": "Depois de verbos como 'enjoy', use a forma com -ing.",
            "focus_past": "Troque verbos irregulares para a forma do passado quando falar de eventos passados.",
            "focus_review": "Revise a correção principal acima e tente o mesmo padrão em uma nova frase.",
            "why_enjoy": "Depois de 'enjoy', use o gerúndio (-ing) e não o infinitivo (to + verbo).",
            "why_past": "Use o passado simples 'went' para ações passadas, e não a forma base 'go'.",
            "why_good_like": "Boa estrutura de frase! 'I like' está corretamente seguido pelo gerúndio.",
            "grammar_check": "Revise a estrutura da sua frase para ganhar mais clareza.",
            "verb_tense_explanation": "Use o passado simples com 'yesterday'.",
            "word_choice_explanation": "Tente uma palavra mais natural aqui.",
        },
        "es": {
            "spot_change": "Puedes detectar qué palabra debe cambiar antes de enviarla?",
            "add_detail": "Qué detalle extra podría hacer tu idea más clara?",
            "polish_form": "La idea principal ya está. Ahora ajusta la forma.",
            "expand_clear": "Tu mensaje está claro. Intenta ampliarlo con un detalle más.",
            "good_start": "Buen comienzo!",
            "almost_there": "Casi listo. Revisa la gramática.",
            "nice_try": "Buen intento!",
            "great_job": "Muy bien! Tu oración está bien estructurada.",
            "excellent_work": "Excelente trabajo! Sigue practicando.",
            "doing_great": "Lo estás haciendo muy bien!",
            "past_question": "Qué palabra en tu oración le dice al oyente que la acción ocurrió en el pasado?",
            "detail_question": "Qué detalle extra podría hacer tu mensaje más preciso?",
            "retry_pattern": "Estás cerca. Intenta una oración más con el mismo patrón.",
            "keep_clarity": "Buen trabajo. Mantén esa claridad en tu próxima respuesta.",
            "summary_past": "Buena práctica con el pasado! Recuerda usar correctamente los verbos irregulares.",
            "summary_future": "Buen trabajo con las formas de futuro! Sigue practicando los patrones con 'will' y 'going to'.",
            "summary_present": "Buen uso del present continuous para acciones que ocurren ahora!",
            "summary_hobbies": "Excelente vocabulario para hablar de intereses y actividades!",
            "summary_work": "Tu lenguaje profesional está mejorando bien! Sigue ampliando el vocabulario de trabajo.",
            "summary_weekend": "Buen uso de expresiones de tiempo futuro! Tu vocabulario de planificación es claro.",
            "summary_start": "Buen comienzo! Enfócate en la estructura básica de la oración y el orden de palabras.",
            "summary_default": "Buen esfuerzo! Sigue practicando para ganar confianza y fluidez.",
            "strength_preferences": "Usaste un patrón de oración claro para hablar de preferencias.",
            "strength_understandable": "Tu mensaje principal se entiende, y esa es la parte más difícil de la conversación real.",
            "strength_clear": "Tu oración comunica la idea con claridad.",
            "focus_enjoy": "Después de verbos como 'enjoy', usa la forma en -ing.",
            "focus_past": "Cambia los verbos irregulares a la forma pasada cuando describas eventos pasados.",
            "focus_review": "Revisa la corrección principal de arriba e intenta el mismo patrón en una nueva oración.",
            "why_enjoy": "Después de 'enjoy', usa el gerundio (-ing) y no el infinitivo (to + verbo).",
            "why_past": "Usa el pasado simple 'went' para acciones pasadas, no la forma base 'go'.",
            "why_good_like": "Buena estructura de oración! 'I like' va correctamente seguido por el gerundio.",
            "grammar_check": "Revisa la estructura de tu oración para mejorar la claridad.",
            "verb_tense_explanation": "Usa el pasado simple con 'yesterday'.",
            "word_choice_explanation": "Prueba una palabra más natural aquí.",
        },
        "fr": {
            "spot_change": "Peux-tu repérer le mot qui doit changer avant d'envoyer ?",
            "add_detail": "Quel détail supplémentaire pourrait rendre ton idée plus claire ?",
            "polish_form": "L'idée principale est déjà là. Maintenant, améliore la forme.",
            "expand_clear": "Ton message est clair. Essaie d'ajouter un petit détail.",
            "good_start": "Bon début !",
            "almost_there": "Tu y es presque. Vérifie la grammaire.",
            "nice_try": "Bonne tentative !",
            "great_job": "Très bien ! Ta phrase est bien structurée.",
            "excellent_work": "Excellent travail ! Continue à pratiquer.",
            "doing_great": "Tu progresses très bien !",
            "past_question": "Quel mot dans ta phrase montre que l'action s'est passée dans le passé ?",
            "detail_question": "Quel détail supplémentaire pourrait rendre ton message plus précis ?",
            "retry_pattern": "Tu es proche. Essaie encore une phrase avec le même modèle.",
            "keep_clarity": "Bon travail. Garde cette clarté dans ta prochaine réponse.",
            "summary_past": "Bonne pratique du passé ! Pense à utiliser correctement les verbes irréguliers.",
            "summary_future": "Bon travail sur les formes du futur ! Continue à pratiquer les structures avec 'will' et 'going to'.",
            "summary_present": "Très bon usage du present continuous pour parler d'actions en cours !",
            "summary_hobbies": "Excellent vocabulaire pour parler des centres d'intérêt et des activités !",
            "summary_work": "Ton langage professionnel progresse bien ! Continue à enrichir le vocabulaire du travail.",
            "summary_weekend": "Bon usage des expressions de temps futur ! Ton vocabulaire de planification est clair.",
            "summary_start": "Très bon début ! Concentre-toi sur la structure de base de la phrase et l'ordre des mots.",
            "summary_default": "Bon effort ! Continue à pratiquer pour gagner en confiance et en fluidité.",
            "strength_preferences": "Tu as utilisé une structure claire pour parler de préférences.",
            "strength_understandable": "Ton message principal est compréhensible, et c'est le plus difficile dans une vraie conversation.",
            "strength_clear": "Ta phrase communique l'idée clairement.",
            "focus_enjoy": "Après des verbes comme 'enjoy', utilise la forme en -ing.",
            "focus_past": "Passe les verbes irréguliers au passé quand tu décris des événements passés.",
            "focus_review": "Revois la correction principale ci-dessus et réessaie le même modèle dans une nouvelle phrase.",
            "why_enjoy": "Après 'enjoy', utilise le gérondif (-ing) et non l'infinitif (to + verbe).",
            "why_past": "Utilise le passé simple 'went' pour des actions passées, pas la forme de base 'go'.",
            "why_good_like": "Bonne structure de phrase ! 'I like' est correctement suivi du gérondif.",
            "grammar_check": "Revois la structure de ta phrase pour gagner en clarté.",
            "verb_tense_explanation": "Utilise le passé simple avec 'yesterday'.",
            "word_choice_explanation": "Essaie ici un mot plus naturel.",
        },
    }
    language_pack = translations.get(language, translations["en"])
    return language_pack.get(key, translations["en"][key])


async def micro_eval(
    context: str,
    lesson_frame: Dict[str, Any],
    draft: str,
    student_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock micro-evaluation of student's draft using unified text analysis.

    Returns stable scores and issues that match what chat_stream would say.
    Uses _analyze_text() to ensure coherence with chat responses.
    """
    # Use unified text analysis
    analysis = _analyze_text(draft, lesson_frame)

    # Generate pseudo-random but stable scores based on draft content
    score_seed = sum(ord(c) for c in draft) % 100

    # Create LOCAL RNG (does not affect other methods)
    rng = random.Random(score_seed)

    # Base scores with some variation but generally tied to detected errors
    has_errors = len(analysis["detected_errors"]) > 0

    if has_errors:
        grammar_score = 40 + (rng.randint(0, 99) % 30)  # 40-70 (has errors)
        spelling_score = 70 + (rng.randint(0, 99) % 30)  # 70-100
        naturalness_score = 40 + (rng.randint(0, 99) % 40)  # 40-80
        lesson_alignment_score = 50 + (rng.randint(0, 99) % 40)  # 50-90
    else:
        grammar_score = 80 + (rng.randint(0, 99) % 20)  # 80-100 (good)
        spelling_score = 85 + (rng.randint(0, 99) % 15)  # 85-100
        naturalness_score = 70 + (rng.randint(0, 99) % 30)  # 70-100
        lesson_alignment_score = 70 + (rng.randint(0, 99) % 30)  # 70-100

    # Generate issues from detected_errors in analysis
    issues = []

    for error in analysis["detected_errors"][:3]:  # Max 3 issues
        # Use canonical category from analysis (grammar, style, etc)
        # NOT the error type (contraction, punctuation, etc.)
        category = error.get("category", "grammar")

        issue = {
            "category": category,
            "title": error.get("original", "Error").capitalize(),
            "explanation": _microcopy(student_profile, "verb_tense_explanation")
            if category == "grammar"
            else _microcopy(student_profile, "word_choice_explanation"),
            "highlight_spans": [error.get("span", {})] if error.get("span") else [],
            "suggestions": [error.get("correction", "Try again")]
        }
        issues.append(issue)

    # If no detected errors but scores are low, add generic issues
    if not issues and grammar_score < 60:
        issues.append({
            "category": "grammar",
            "title": "Grammar check",
            "explanation": _microcopy(student_profile, "grammar_check"),
            "highlight_spans": [],
            "suggestions": ["Check verb tenses", "Review word order"]
        })

    # Suggested next words based on topic and keywords
    suggestions_by_topic = {
        "past_simple": ["went", "played", "visited", "stayed", "traveled", "watched", "cooked", "studied"],
        "future": ["will", "going to", "plan", "expect", "hope"],
        "present_continuous": ["doing", "working", "playing", "studying", "reading"],
        "hobbies": ["enjoy", "practice", "love", "prefer"],
        "work": ["job", "office", "company", "meetings", "projects"],
        "weekend_plans": ["relax", "visit", "travel", "rest", "explore"]
    }

    topic = analysis["topic"]
    suggestions_pool = suggestions_by_topic.get(topic, ["continue", "practice", "improve"])
    suggested_next_words = rng.sample(suggestions_pool, min(3, len(suggestions_pool)))

    # Micro tip based on performance
    if has_errors:
        micro_tips = [
            f"{_microcopy(student_profile, 'good_start')} {analysis['correction_text']}",
            _microcopy(student_profile, "almost_there"),
            f"{_microcopy(student_profile, 'nice_try')} {analysis['correction_text']}",
        ]
    else:
        micro_tips = [
            _microcopy(student_profile, "great_job"),
            _microcopy(student_profile, "excellent_work"),
            _microcopy(student_profile, "doing_great"),
        ]

    micro_tip = rng.choice(micro_tips)
    self_check_prompt = (
        _microcopy(student_profile, "spot_change")
        if has_errors
        else _microcopy(student_profile, "add_detail")
    )
    encouragement = (
        _microcopy(student_profile, "polish_form")
        if has_errors
        else _microcopy(student_profile, "expand_clear")
    )

    return {
        "grammar_score": float(grammar_score),
        "spelling_score": float(spelling_score),
        "naturalness_score": float(naturalness_score),
        "lesson_alignment_score": float(lesson_alignment_score),
        "top_issues": issues[:3],  # Max 3 issues
        "suggested_next_words": suggested_next_words,
        "micro_tip": micro_tip,
        "self_check_prompt": self_check_prompt,
        "encouragement": encouragement,
        # Rich signals for analysis panel
        "topic": analysis.get("topic"),
        "intent": analysis.get("intent"),
        "rewrite": analysis.get("rewrite")
    }


async def autocomplete(
    context: str,
    lesson_frame: Dict[str, Any],
    draft: str,
    student_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock ghost suggestion (1-6 words) using inferred topic.

    Returns a short continuation based on analyzed topic and last word.
    Uses _analyze_text() for topic inference.
    """
    # Use unified text analysis to get topic
    analysis = _analyze_text(draft, lesson_frame)
    topic = analysis["topic"]

    # Pseudo-random but deterministic based on draft
    suggestion_seed = sum(ord(c) for c in draft) % 10

    # Create LOCAL RNG (does not affect other methods)
    rng = random.Random(suggestion_seed)

    # Suggestions by topic (contextual)
    suggestions_map = {
        "past_simple": ["went to the", "yesterday", "last week", "visited", "stayed at", "traveled to"],
        "future": ["will go", "going to", "tomorrow", "next week", "plan to"],
        "present_continuous": ["am doing", "is working", "are playing", "currently", "right now"],
        "hobbies": ["enjoy", "practice", "love to", "my favorite"],
        "work": ["at the office", "for my job", "in the company", "during work"],
        "weekend_plans": ["this weekend", "on Saturday", "tomorrow", "next Sunday"],
        "getting_started": ["more", "and then", "also", "next"],
        "default": ["more", "and then", "also", "continue", "next"]
    }

    # Pick suggestion based on topic
    suggestions = suggestions_map.get(topic, suggestions_map["default"])
    ghost_suggestion = rng.choice(suggestions)

    return {
        "ghost_suggestion": ghost_suggestion,
        "reason": f"Based on detected topic: {topic}"
    }


async def generate_teacher_analysis(
    user_message: str,
    context: str,
    lesson_frame: Dict[str, Any],
    student_profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate teacher analysis as JSON (separate from chat reply).

    Returns structured analysis with:
    - rewrite: Corrected version of user's message
    - corrections: List of {mistake, fix, why}
    - teacher_summary: Brief pedagogical feedback
    - next_practice: 2-3 suggested practice sentences
    """
    # Analyze user message to detect common errors
    analysis = _analyze_text(user_message, lesson_frame)
    topic = analysis["topic"]

    # Detect common errors and generate corrections
    corrections = []
    rewrite = user_message
    strengths = []
    focus_areas = []

    # Check for common mistakes
    if "enjoyed to" in user_message.lower():
        corrections.append({
            "mistake": "enjoyed to sleep",
            "fix": "enjoyed sleeping",
            "why": _microcopy(student_profile, "why_enjoy"),
        })
        rewrite = user_message.replace("enjoyed to sleep", "enjoyed sleeping")
        focus_areas.append(_microcopy(student_profile, "focus_enjoy"))

    elif "went to" in user_message.lower() and "go" in user_message.lower():
        corrections.append({
            "mistake": "go to",
            "fix": "went to",
            "why": _microcopy(student_profile, "why_past"),
        })
        rewrite = user_message.replace("go to", "went to")
        focus_areas.append(_microcopy(student_profile, "focus_past"))

    elif "i like" in user_message.lower():
        corrections.append({
            "mistake": user_message,
            "fix": user_message,
            "why": _microcopy(student_profile, "why_good_like"),
        })
        strengths.append(_microcopy(student_profile, "strength_preferences"))

    # Generate teacher summary based on topic
    teacher_summaries = {
        "past_simple": _microcopy(student_profile, "summary_past"),
        "future": _microcopy(student_profile, "summary_future"),
        "present_continuous": _microcopy(student_profile, "summary_present"),
        "hobbies": _microcopy(student_profile, "summary_hobbies"),
        "work": _microcopy(student_profile, "summary_work"),
        "weekend_plans": _microcopy(student_profile, "summary_weekend"),
        "getting_started": _microcopy(student_profile, "summary_start"),
        "default": _microcopy(student_profile, "summary_default"),
    }

    teacher_summary = teacher_summaries.get(topic, teacher_summaries["default"])
    if not strengths:
        if corrections:
            strengths.append(_microcopy(student_profile, "strength_understandable"))
        else:
            strengths.append(_microcopy(student_profile, "strength_clear"))
    if not focus_areas and corrections:
        focus_areas.append(_microcopy(student_profile, "focus_review"))

    # Generate next practice sentences based on topic
    practice_sentences_map = {
        "past_simple": [
            "I _____ (go) to the cinema yesterday.",
            "She _____ (eat) pizza last night.",
            "We _____ (see) a beautiful sunset."
        ],
        "future": [
            "Tomorrow I _____ (visit) my grandmother.",
            "Next week we _____ (travel) to the beach.",
            "I _____ (study) English tonight."
        ],
        "present_continuous": [
            "Now I _____ (read) a book.",
            "She _____ (work) on her project.",
            "They _____ (play) football in the park."
        ],
        "hobbies": [
            "I enjoy _____ (paint) in my free time.",
            "My hobby is _____ (play) the guitar.",
            "I love _____ (cook) Italian food."
        ],
        "default": [
            "Practice makes perfect!",
            "Keep up the good work!",
            "Try another example."
        ]
    }

    next_practice = practice_sentences_map.get(topic, practice_sentences_map["default"])
    reflection_question = (
        _microcopy(student_profile, "past_question")
        if topic == "past_simple"
        else _microcopy(student_profile, "detail_question")
    )
    encouragement = (
        _microcopy(student_profile, "retry_pattern")
        if corrections
        else _microcopy(student_profile, "keep_clarity")
    )

    return {
        "rewrite": rewrite,
        "corrections": corrections,
        "teacher_summary": teacher_summary,
        "strengths": strengths[:3],
        "focus_areas": focus_areas[:3],
        "next_practice": next_practice[:3],  # Max 3 practice sentences
        "reflection_question": reflection_question,
        "encouragement": encouragement,
    }
