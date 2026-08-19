---
name: encyclopedia-translator
description: Translate documents between languages with high quality. Use when asked to translate text, documents, articles, or any content from one language to another. Supports Chinese, English, Japanese, Korean, French, German, Spanish, Portuguese, Russian, Arabic, Thai, Vietnamese, Indonesian, Malay, Hindi, and more.
---

# Encyclopedia Translator

## Goal

Translate documents between languages while preserving meaning, tone, style, and cultural nuances. This skill aims to provide professional-grade translation that goes beyond word-for-word conversion, taking into account context, idiomatic expressions, domain-specific terminology, and target audience expectations.

## Background and Theory

### What is Translation?

Translation is the process of converting text from one language (the source language) to another language (the target language). Good translation is not simply replacing words — it requires understanding the meaning, context, and intent behind the original text.

### The History of Machine Translation

Machine translation has evolved through several paradigms:

1. **Rule-based Machine Translation (RBMT)** — 1950s-1990s
   - Uses linguistic rules and dictionaries
   - Pros: Predictable, handles rare languages
   - Cons: Requires extensive hand-crafted rules, poor fluency
   - Examples: SYSTRAN, Apertium

2. **Statistical Machine Translation (SMT)** — 1990s-2010s
   - Uses statistical models trained on parallel corpora
   - Key technique: phrase-based translation with language models
   - Pros: Better fluency, data-driven
   - Cons: Requires large parallel corpora, struggles with rare words
   - Examples: Moses, early Google Translate

3. **Neural Machine Translation (NMT)** — 2014-present
   - Uses deep learning models (initially RNNs, now Transformers)
   - Key breakthrough: Attention mechanism (Bahdanau et al., 2014)
   - Transformer architecture (Vaswani et al., 2017) — "Attention Is All You Need"
   - Pros: Much better fluency and accuracy
   - Cons: Requires large compute, can hallucinate
   - Examples: Google Neural Machine Translation, DeepL

4. **Large Language Model Translation (LLM-based)** — 2022-present
   - Uses general-purpose LLMs like GPT-4, Claude, Gemini
   - Can follow complex translation instructions
   - Supports context-aware, style-specific translation
   - Pros: Highly flexible, handles nuance well
   - Cons: Expensive, slower than dedicated MT systems

### Translation Quality Metrics

Several metrics are commonly used to evaluate translation quality:

- **BLEU (Bilingual Evaluation Understudy)**: Measures n-gram overlap with reference translations. Score range: 0-100. A score above 30 is generally considered reasonable for most language pairs.

- **METEOR**: Considers synonyms and paraphrases in addition to exact matches. Generally correlates better with human judgments than BLEU.

- **TER (Translation Edit Rate)**: Measures the number of edits needed to change the machine translation output to match a reference. Lower is better.

- **COMET**: A neural metric trained on human quality assessments. Currently considered the most reliable automatic metric.

- **Human Evaluation**: The gold standard. Usually involves:
  - Adequacy: Does the translation preserve the meaning?
  - Fluency: Does the translation read naturally?
  - Overall quality: Professional-grade or not?

### The Seven Principles of Good Translation

Based on decades of translation theory and practice, good translation follows these principles:

1. **Accuracy**: The translation must faithfully convey the meaning of the source text
2. **Naturalness**: The translation should read as if originally written in the target language
3. **Consistency**: Terminology should be consistent throughout the document
4. **Completeness**: Nothing should be omitted or added without reason
5. **Cultural Adaptation**: Cultural references should be appropriately localized
6. **Register Matching**: The formality level should match the source
7. **Domain Awareness**: Technical terms should be translated according to domain conventions

### Common Translation Challenges

#### Challenge 1: Idiomatic Expressions

Every language has idiomatic expressions that cannot be translated literally:
- English: "It's raining cats and dogs" → Chinese: "倾盆大雨" (not "下猫下狗")
- Chinese: "对牛弹琴" → English: "Casting pearls before swine" (not "playing music to a cow")
- Japanese: "猫の手も借りたい" → English: "So busy I could use any help" (not "want to borrow a cat's paw")

The key is to identify the underlying meaning and find an equivalent expression in the target language.

#### Challenge 2: Ambiguity

Source text may be ambiguous, and different interpretations lead to different translations:
- English "bank" → Chinese "银行" (financial) or "河岸" (river)
- English "right" → Chinese "正确的" (correct) or "右边的" (direction) or "权利" (entitlement)
- Chinese "他" → English "he/him" or "she/her" or "they/them" (in classical Chinese, 他 was gender-neutral)

Context is essential for resolving ambiguity.

#### Challenge 3: Untranslatable Concepts

Some concepts don't have direct equivalents:
- Japanese "侘び寂び" (wabi-sabi) — aesthetic of imperfection and transience
- Portuguese "saudade" — deep emotional longing
- German "Schadenfreude" — pleasure from others' misfortune
- Danish "hygge" — cozy contentment
- Chinese "缘分" — predestined affinity

For these, translators typically use: borrowing, explanation, or approximation.

#### Challenge 4: Technical Terminology

Different domains have specific terminology that must be consistent:
- "Memory" in CS: 内存 — in psychology: 记忆
- "Cell" in biology: 细胞 — in electronics: 电池 — in prison: 牢房
- "Protocol" in networking: 协议 — in diplomacy: 礼仪

Maintaining a glossary is essential for technical translation.

#### Challenge 5: Style and Register

The same content can be expressed at different formality levels:
- Casual: "This thing doesn't work"
- Standard: "This feature is not functioning properly"
- Formal: "We regret to inform you that the aforementioned functionality is currently experiencing an operational deficiency"

The translator must match the register of the source text.

### Language-Specific Notes

#### Chinese-English Translation Notes

When translating between Chinese and English, pay special attention to:

1. **Sentence Structure**: Chinese is typically SVO but allows more flexible word order. English has stricter word order requirements.
2. **Topic-Comment Structure**: Chinese often uses topic-comment structure (这个问题，我已经解决了 = "This problem, I have already solved it")
3. **Measure Words**: Chinese requires measure words (量词) that don't exist in English (一条狗, 一本书, 一台电脑)
4. **Tense**: Chinese doesn't conjugate verbs for tense; context and time words indicate when something happened
5. **Politeness**: Chinese has complex politeness systems (您 vs 你, formal vs casual language)
6. **Numbers and Units**: Different counting systems (万 = 10,000 instead of grouping by thousands)
7. **Names**: Chinese names are family name first; deciding whether to keep Chinese order or switch to Western order

#### Japanese-English Translation Notes

1. **SOV Word Order**: Japanese is Subject-Object-Verb, opposite to English SVO
2. **Honorific System**: Keigo (敬語) has three levels that affect verb conjugation
3. **Context-Heavy**: Japanese frequently omits subjects when they're contextually clear
4. **Writing Systems**: Mix of kanji, hiragana, katakana affects rendering decisions
5. **Sentence-Final Particles**: particles like ね, よ, ぞ convey nuance hard to translate

#### Korean-English Translation Notes

1. **SOV Word Order**: Similar to Japanese
2. **Honorific Levels**: Seven speech levels in Korean
3. **Agglutinative**: Words are built by adding suffixes
4. **Subject Omission**: Common in conversational Korean

### Document Format Handling

#### Markdown Documents
- Preserve all Markdown formatting (headers, bold, italic, code blocks)
- Don't translate content inside code blocks
- Translate alt text for images
- Preserve link URLs, translate link text

#### JSON/YAML Files
- Only translate string values, not keys
- Preserve structure and formatting
- Handle escape characters properly

#### HTML Content
- Translate visible text content
- Preserve all HTML tags and attributes
- Handle entities properly (&amp;, &lt;, etc.)
- Don't translate class names or IDs

#### PDF Documents
- Extract text first, then translate
- Note any formatting that may be lost
- Handle tables and columns carefully

## Workflow

1. **Detect source language** — identify the language of the input text
2. **Identify document type** — markdown, plain text, JSON, HTML, or PDF
3. **Analyze domain** — technical, literary, casual, formal, legal, medical
4. **Apply translation** — translate while preserving formatting and structure
5. **Quality check** — review for accuracy, naturalness, and completeness
6. **Deliver result** — output translated text with any notes

## Constraints

- Always preserve the original formatting
- Never add content that wasn't in the original
- Maintain consistent terminology throughout
- Flag any ambiguous or uncertain translations
- Keep code blocks, URLs, and file paths untranslated

## Validation

- Translation preserves the original meaning
- Formatting is maintained
- Technical terms are correctly translated
- No content is missing or added
