# Demo examples (tested on the final model, 21 Nov)

Start the app with `python run_app.py`, open **Report an incident**, type or paste a message and press **Enter**.
None of these sentences is in the training data. Output checked with `python -m src.quick_check`.

| # | Type or paste this | Expected top result |
|---|---|---|
| 1 | Kal raat do larke motorcycle par aaye aur pistol dikha kar meri behan ka purse aur mobile chheen kar bhaag gaye | **392** Robbery (99%) |
| 2 | My neighbour broke our boundary wall and started building a room on our plot, he says the land is his now | **447** Criminal Trespass (99%) |
| 3 | Mere customer ne 4 lakh ka cheque diya tha, bank ne insufficient funds keh kar wapas kar diya | **489-F** Dishonoured Cheque (100%) |
| 4 | A man on Facebook sold me a phone, I sent 80,000 through JazzCash and he blocked me | **420** Cheating / Fraud (86%) |
| 5 | Mere shohar ne kal mujhe belt se mara, baazu aur kamar pe zakhm hain | **337-F** Jurh (100%) |
| 6 | My colleague keeps sending me vulgar messages at night and makes dirty comments about my body | **509** (100%), with the "anyone, including at work" note |
| 7 | Pados wale ne kaha agar case wapas na liya to tujhe aur tere bachon ko jaan se maar dunga | **506** Criminal Intimidation (99%) |
| 8 | Hum shaadi par gaye thay, peeche se chor ghar ka tala tor kar almari se zewar aur cash le gaye | **380** Theft in Dwelling House (99%) |
| 9 | Mere bete ko school ke bahar se kisi ne utha liya aur ab phone kar ke 20 lakh maang rahe hain | **365-A** Kidnapping for Ransom (100%) |
| 10 | A gang calls my shop every month demanding 50,000 or they will burn it, I paid them last month | **384** Extortion (85%) |
| 11 | My cousin is telling everyone in the family that I stole money from my uncle, which is a lie, and people have stopped talking to me | **500** Defamation (93%) |
| 12 | Mujhe mere seth ne dukaan ke store mein do din band rakha aur bahar nahi nikalne diya | **340** Wrongful Confinement (98%) |
| 13 | Six armed men entered our house at night, tied everyone up and took all the gold and cash | **395** Dacoity (99%) |
| 14 | mujhe kl mere roommate ne bohat mara aur dhamki di k kisi ko bataya to phir maregi | **506** (98%) + **337-F** (88%): two offences |
| 15 | teacher wont give me marks | **Refused** (not confident, asks for detail) |
| 16 | My landlord increased the rent this month | **Refused** |

**Good order for a live demo:** 1 (Roman Urdu robbery) → 14 (chat spelling, two offences) → 6 (the 509 note) →
15 (refuses instead of guessing) → then on #1 open "Why this result?", the Supreme Court cases, the police
application and the PDF → Student Corner: a topic, Look-alikes, a 5-question quiz to the results screen.

## Limitations to say openly

- **Training data is small and mostly not real citizen text:** 1,873 training rows; citizen-style messages are
  AI-written (reviewed); Pakistani data = 142 Supreme Court of Pakistan judgments; the rest are Indian judgments
  (ILSI), mapped to PPC. The test set is 98% AI-written (`docs/round2_data.md`).
- **Real messages tested: only 11** (3 in J1 + 8 in the hands-on check). Safe (no wrong answers on the 8) but
  cautious: it refuses some real crimes it could answer (D31).
- **No "not a crime" class:** some everyday disputes can still get an answer (D30); a gate needs much more
  non-crime data.
- **30 offences only;** special laws (PECA, harassment at the workplace act, etc.) and the Constitution are future work.
- **Legal information, not legal advice:** the app always says so and points to 1099.
