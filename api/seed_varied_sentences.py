#!/usr/bin/env python3
"""
Seed varied sentences for words according to Spec4 requirements
Each word should have multiple different sentences for variety
"""

from app.core.database import SessionLocal
from app.models import Word, Sentence, WordSentence, Language, Card, Deck
from app.models.sentence import SourceType
import uuid
import random


def seed_varied_sentences():
    """Seed multiple sentences per word for variety"""

    db = SessionLocal()
    try:
        # Get English language
        en_lang = db.query(Language).filter(Language.code == 'en').first()
        if not en_lang:
            print("English language not found")
            return False

        # Get or create default deck for English
        deck = db.query(Deck).filter(
            Deck.language_id == en_lang.id,
            Deck.is_active == True
        ).first()

        if not deck:
            deck = Deck(
                id=str(uuid.uuid4()),
                name=f"Spec4 Seed {en_lang.code.upper()}",
                language_id=en_lang.id,
                difficulty_level=1,
                description="Auto-generated deck for Spec4 varied sentences",
                is_active=True
            )
            db.add(deck)
            db.flush()
            print(f"Created new deck: {deck.id}")

        # Common words with multiple example sentences
        word_sentences_data = [
            # High frequency words - multiple examples each
            ("the", [
                ("The cat is sleeping on the couch.", "O gato está dormindo no sofá.", "determiner", 1),
                ("I love the weather today.", "Eu amo o clima hoje.", "determiner", 1),
                ("The book you gave me was amazing.", "O livro que você me deu foi incrível.", "determiner", 1),
                ("She works at the best company in town.", "Ela trabalha na melhor empresa da cidade.", "determiner", 1),
                ("The children are playing outside.", "As crianças estão brincando lá fora.", "determiner", 1),
            ]),
            ("be", [
                ("I want to be a doctor when I grow up.", "Eu quero ser médico quando crescer.", "verb, base form", 1),
                ("To be honest, I don't like this movie.", "Para ser honesto, eu não gosto deste filme.", "verb, infinitive", 2),
                ("She was happy to see her friends.", "Ela estava feliz em ver seus amigos.", "verb, past tense", 1),
                ("They will be here in five minutes.", "Eles estarão aqui em cinco minutos.", "verb, future", 1),
                ("Being kind is important in life.", "Ser gentil é importante na vida.", "verb, gerund", 2),
            ]),
            ("have", [
                ("I have a new car.", "Eu tenho um carro novo.", "verb, present", 1),
                ("She had to leave early today.", "Ela teve que sair cedo hoje.", "verb, past", 1),
                ("Having friends makes life better.", "Ter amigos torna a vida melhor.", "verb, gerund", 2),
                ("They have been waiting for an hour.", "Eles estão esperando há uma hora.", "verb, present perfect", 2),
                ("We will have enough food for everyone.", "Nós teremos comida suficiente para todos.", "verb, future", 2),
            ]),
            ("do", [
                ("What do you want for dinner?", "O que você quer para o jantar?", "verb, present", 1),
                ("She did her homework yesterday.", "Ela fez sua lição de casa ontem.", "verb, past", 1),
                ("Doing exercise every day is healthy.", "Fazer exercício todo dia é saudável.", "verb, gerund", 2),
                ("I don't know what to do.", "Eu não sei o que fazer.", "verb, negative", 1),
                ("They did a great job on the project.", "Eles fizeram um ótimo trabalho no projeto.", "verb, past", 1),
            ]),
            ("say", [
                ("Can you say that again, please?", "Você pode dizer isso novamente, por favor?", "verb, present", 1),
                ("She said she would call me tomorrow.", "Ela disse que me ligaria amanhã.", "verb, past", 1),
                ("Saying the right thing at the right time is important.", "Dizer a coisa certa na hora certa é importante.", "verb, gerund", 2),
                ("What did the teacher say about the exam?", "O que o professor disse sobre a prova?", "verb, past", 1),
                ("I always say what I think.", "Eu sempre digo o que penso.", "verb, present", 1),
            ]),
            ("go", [
                ("I go to work every day by bus.", "Eu vou para o trabalho todo dia de ônibus.", "verb, present", 1),
                ("She went to the store yesterday.", "Ela foi à loja ontem.", "verb, past", 1),
                ("Going on vacation is always exciting.", "Ir de férias é sempre emocionante.", "verb, gerund", 2),
                ("They will go to the beach next weekend.", "Eles irão à praia no próximo fim de semana.", "verb, future", 1),
                ("Let's go get some ice cream.", "Vamos pegar sorvete.", "verb, imperative", 1),
            ]),
            ("get", [
                ("I get up at 6 AM every morning.", "Eu levanto às 6 AM toda manhã.", "verb, present", 1),
                ("She got a promotion at work.", "Ela conseguiu uma promoção no trabalho.", "verb, past", 1),
                ("Getting enough sleep is important for health.", "Dormir o suficiente é importante para a saúde.", "verb, gerund", 2),
                ("They will get married next year.", "Eles se casarão no próximo ano.", "verb, future", 1),
                ("Can you get me a glass of water?", "Você pode me pegar um copo de água?", "verb, present", 1),
            ]),
            ("make", [
                ("I make breakfast for my family every Sunday.", "Eu preparo café da manhã para minha família todo domingo.", "verb, present", 1),
                ("She made a beautiful painting for her mother.", "Ela fez uma pintura linda para sua mãe.", "verb, past", 1),
                ("Making mistakes is part of learning.", "Cometer erros é parte do aprendizado.", "verb, gerund", 2),
                ("They will make a decision soon.", "Eles tomarão uma decisão em breve.", "verb, future", 1),
                ("This makes me very happy.", "Isso me faz muito feliz.", "verb, present", 1),
            ]),
            ("know", [
                ("I know the answer to this question.", "Eu sei a resposta para esta pergunta.", "verb, present", 1),
                ("She knew all the words to the song.", "Ela sabia todas as palavras da música.", "verb, past", 1),
                ("Knowing yourself is the first step to wisdom.", "Conhecer a si mesmo é o primeiro passo para a sabedoria.", "verb, gerund", 2),
                ("Do you know how to get to the station?", "Você sabe como chegar à estação?", "verb, present", 1),
                ("I wish I knew more about history.", "Eu gostaria de saber mais sobre história.", "verb, subjunctive", 2),
            ]),
            # Medium frequency words
            ("water", [
                ("I need a glass of water.", "Eu preciso de um copo de água.", "noun", 1),
                ("The flowers need more water.", "As flores precisam de mais água.", "noun", 1),
                ("She drinks eight glasses of water every day.", "Ela bebe oito copos de água todo dia.", "noun", 1),
                ("Water covers most of the Earth's surface.", "A água cobre a maior parte da superfície da Terra.", "noun", 2),
                ("Don't forget to water the plants.", "Não se esqueça de regar as plantas.", "verb", 1),
            ]),
            ("time", [
                ("What time is it?", "Que horas são?", "noun", 1),
                ("We had a great time at the party.", "Nós tivemos um ótimo tempo na festa.", "noun", 1),
                ("Time flies when you're having fun.", "O tempo voa quando você está se divertindo.", "noun", 2),
                ("She doesn't have time to talk right now.", "Ela não tem tempo para conversar agora.", "noun", 1),
                ("Time heals all wounds.", "O tempo cura todas as feridas.", "noun", 3),
            ]),
            ("work", [
                ("I go to work by train.", "Eu vou para o trabalho de trem.", "noun", 1),
                ("She works from home on Mondays.", "Ela trabalha de casa às segundas.", "verb", 1),
                ("Hard work always pays off.", "Trabalho duro sempre compensa.", "noun", 2),
                ("They are working on a new project.", "Eles estão trabalhando em um novo projeto.", "verb", 1),
                ("This computer doesn't work properly.", "Este computador não funciona corretamente.", "verb", 1),
            ]),
            ("book", [
                ("I'm reading a good book.", "Estou lendo um bom livro.", "noun", 1),
                ("She booked a flight to Paris.", "Ela reservou um voo para Paris.", "verb", 1),
                ("The library has many interesting books.", "A biblioteca tem muitos livros interessantes.", "noun", 1),
                ("Can you book a table for two at 8 PM?", "Você pode reservar uma mesa para duas às 8 PM?", "verb", 2),
                ("Don't judge a book by its cover.", "Não julgue um livro pela capa.", "noun", 3),
            ]),
            ("family", [
                ("My family lives in another city.", "Minha família mora em outra cidade.", "noun", 1),
                ("She spends weekends with her family.", "Ela passa fins de semana com sua família.", "noun", 1),
                ("Family is the most important thing in life.", "Família é a coisa mais importante na vida.", "noun", 2),
                ("They are a very close family.", "Eles são uma família muito unida.", "noun", 1),
                ("How many people are in your family?", "Quantas pessoas estão na sua família?", "noun", 1),
            ]),
        ]

        created_count = 0
        updated_count = 0

        for word_text, sentences_data in word_sentences_data:
            # Find the word
            word = db.query(Word).filter(
                Word.text == word_text,
                Word.language_id == en_lang.id
            ).first()

            if not word:
                print(f"Word '{word_text}' not found, skipping...")
                continue

            # Create sentences for this word
            for sentence_text, translation, grammar_hint, difficulty in sentences_data:
                # Check if this exact sentence already exists
                existing_sentence = db.query(Sentence).filter(
                    Sentence.text == sentence_text
                ).first()

                if existing_sentence:
                    # Create WordSentence mapping if it doesn't exist
                    existing_mapping = db.query(WordSentence).filter(
                        WordSentence.word_id == word.id,
                        WordSentence.sentence_id == existing_sentence.id
                    ).first()

                    if not existing_mapping:
                        mapping = WordSentence(
                            word_id=word.id,
                            sentence_id=existing_sentence.id,
                            is_primary=False
                        )
                        db.add(mapping)
                        updated_count += 1
                    continue

                # Create new sentence
                gap_start = sentence_text.find(word_text)
                gap_end = gap_start + len(word_text)

                if gap_start == -1:
                    # If word not found in sentence, put it in a reasonable position
                    gap_start = sentence_text.find("___")
                    if gap_start == -1:
                        gap_start = 0
                    gap_end = gap_start + len(word_text)

                # Replace word with gap for the sentence
                sentence_text_with_gap = sentence_text[:gap_start] + "___" + sentence_text[gap_end:]

                sentence = Sentence(
                    text=sentence_text_with_gap,
                    translation=translation,
                    word_id=word.id,
                    language_id=en_lang.id,
                    type="example",  # CRITICAL: Sentence.type is required
                    source_type=SourceType.MANUAL,
                    difficulty=difficulty,
                    gap_start=gap_start,
                    gap_end=gap_end,
                    grammar_hint=grammar_hint
                )
                db.add(sentence)
                db.flush()  # Get the ID

                # CRITICAL: Create Card for each Sentence (Spec4 requirement)
                card = Card(
                    id=str(uuid.uuid4()),
                    sentence_id=sentence.id,
                    deck_id=deck.id,
                    grammar_hint=grammar_hint,
                    difficulty=difficulty,
                    gap_start=gap_start,
                    gap_end=gap_end,
                    is_active=True
                )
                db.add(card)
                db.flush()

                # Create WordSentence mapping
                mapping = WordSentence(
                    word_id=word.id,
                    sentence_id=sentence.id,
                    is_primary=len(db.query(WordSentence).filter(WordSentence.word_id == word.id).all()) == 0
                )
                db.add(mapping)
                created_count += 1

        db.commit()

        print(f"Successfully created {created_count} new varied sentences")
        print(f"Successfully updated {updated_count} word-sentence mappings")

        return True

    except Exception as e:
        print(f"Error seeding varied sentences: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = seed_varied_sentences()
    if success:
        print("Varied sentences seeded successfully!")
    else:
        print("Failed to seed varied sentences")