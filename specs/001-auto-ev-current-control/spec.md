# Feature Specification: Automatyczne sterowanie pradem ladowania EV (MVP)

**Feature Branch**: `001-create-spec-branch`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Automatyczne sterowanie pradem ladowania dla pojedynczej instalacji EV, zgodnie z constitution i zakresem MVP"

## Clarifications

### Session 2026-06-13

- Q: Ktora regule uznajemy za kryterium stale data (dane nieaktualne) dla encji wymaganych do decyzji minutowej? -> A: Globalnie sztywny prog 60 s dla wszystkich encji.
- Q: Jak definiujemy minimalna bezpieczna wartosc automatyczna, do ktorej system schodzi przy utracie jakosci danych podczas aktywnego ladowania? -> A: Zawsze 6 A (stala, niekonfigurowalna).
- Q: Jaka ma byc regula rozstrzygania sprzecznych danych krytycznych (np. jednoczesny import i eksport niespojny z bilansem), gdy ladowanie jest aktywne? -> A: Traktuj jako blad krytyczny: zejscie do 6 A i oznaczenie fail-safe.
- Q: Jaka jest minimalna zmiana w sygnatach wejsciowych, ktorej uzasadnia przesuniencie docelowego pradu o 1 A? -> A: Zmiana pokrywajaca zmiane 1 A pradu ladowania na moc; dla pradu trojfazowego ok. 700 W.
- Q: Jak zdefiniowac domyslne limity ceny (buy-price threshold i sell-price threshold) dla trybu economical? -> A: Domyslnie: buy_threshold = 0 (zawsze kupuj), sell_threshold = 0 (zawsze sprzedaj).

### Session 2026-06-14

- Q: Jak system ma wykrywac, ze uzytkownik recznie zmienil zachowanie ladowania (FR-018)? -> A: Porownanie ostatnio zadanego pradu z rzeczywistym pradem raportowanym przez EVSE; rozbiezćnosc >1 A oznacza manual override.- Q: W jaki sposob integracja wydaje polecenie zmiany pradu do EVSE? -> A: Zapis do encji Home Assistant (np. number, select) steujacej EVSE, wskazanej przez uzytkownika w konfiguracji.
- Q: Jakiego rodzaju progi chroniace magazyn energii ma obslugiwac integracja? -> A: Stopniowane progi SoC (ponizej 50%, 70%, 90%) z osobnym, konfigurowalnym limitem maksymalnej mocy rozladowania magazynu dla kazdego przedzialu.
- Q: Jak glęboka ma byc analiza cen przyszlych w trybie economical? -> A: Wszystkie ceny dostepne w atrybutach encji cenowej, bez ograniczenia glebokosci.- Q: Co ma robic integracja bezposrednio po restarcie, gdy EV jest juz podlaczone i ladowanie jest aktywne? -> A: Odczytac tryb pracy z encji HA (tryb jest persisted i odtwarzany po restarcie) i wznowic dzialanie zgodnie z tym trybem bez wymuszania manual ani fail-safe.

### Amendment 2026-06-14

- Wymaganie: system powinien unikac wylaczania ladowania; dodano osobny konfigurowalny prog zatrzymania (bad conditions: rozladowanie magazynu, pobor z sieci) odrebny od fail-safe 6 A.
- Wymaganie: sterowanie ladowarka pokladowa EV (OBC) jako opcjonalny drugi kanal aktuacji; OBC umozliwia ustawienie minimalnego pradu 5 A, co nalezy wykorzystac w sterowaniu.

### Session 2026-06-14 (clarify run 2)

- Q: Gdy OBC jest aktywny, jaka wartosc system wysyla do EVSE jednoczesnie z poleceniem do OBC? -> A: OBC sluzy wylacznie jako dodik ograniczajacy prad do 5 A; EVSE musi byc wczesniej ustawiony na minimum 6 A. Gdy cel wynosi 5 A: EVSE=6 A + OBC=5 A. Dla celow >=6 A: EVSE=cel, OBC nie jest ograniczany (lub nie otrzymuje polecenia).
- Q: Jak unikac flappingu gdy warunek zatrzymania jest przekraczany przez chwilowe skoki? -> A: Dodatkowa histereza: zatrzymaj gdy warunek spelniony przez >=N kolejnych cykli (konfigurowalne N, domyslnie 2).
- Q: Czy logika laczenia sub-progow zatrzymania to OR czy AND? -> A: OR — zatrzymaj gdy ktorykolwiek sub-prog jest przekroczony.
- Q: Czy konfigurowalny prog zatrzymania ladowania (FR-025a) obowiazuje tak samo w trybie fast? -> A: Prog zatrzymania obowiazuje we wszystkich trybach automatycznych, ale wartosci sub-progow sa konfigurowane osobno per tryb (moc rozladowania magazynu, moc importu sieci, cena zakupu z sieci, cena eksportu do sieci).## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bezpieczne automatyczne sterowanie co minute (Priority: P1)

Jako uzytkownik Home Assistant chce skonfigurowac integracje przez wskazanie encji i limitow, aby system automatycznie dostosowywal prad ladowania EV co minute bez przekraczania limitow bezpieczenstwa.

**Why this priority**: To podstawowa wartosc MVP: bezpieczna i przewidywalna automatyka ladowania dla jednej instalacji EV.

**Independent Test**: Mozna przetestowac niezaleznie poprzez dostarczenie poprawnych danych z wymaganych encji, wlaczenie trybu automatycznego i potwierdzenie, ze decyzja o pradzie pojawia sie co minute oraz respektuje limity.

**Acceptance Scenarios**:

1. **Given** uzytkownik skonfigurowal wszystkie wymagane encje oraz limity, **When** automatyka jest aktywna, **Then** system co minute wyznacza docelowy prad ladowania w zakresie dozwolonym przez konfiguracje i ograniczenia techniczne.
2. **Given** obliczony wzrost pradu spowodowalby przekroczenie skonfigurowanego limitu mocy przylacza, **When** system wyznacza decyzje sterujaca, **Then** wzrost jest ograniczany lub odrzucany tak, aby limit mocy przylacza nie zostal przekroczony.
3. **Given** ladowanie jest aktywne i wymagane dane staja sie brakujace, nieaktualne, nieprawidlowe lub sprzeczne, **When** system wykonuje kolejna decyzje, **Then** przechodzi do bezpiecznego minimum automatycznego zamiast kontynuowac agresywna optymalizacje.

---

### User Story 2 - Sterowanie zalezne od trybu pracy (Priority: P2)

Jako uzytkownik chce wybierac tryb pracy (balanced, fast, economical, manual), aby automatyka realizowala rozne priorytety po zachowaniu stalych zasad bezpieczenstwa i przewidywalnosci.

**Why this priority**: Tryby pracy definiuja oczekiwane zachowanie biznesowe i pozwalaja dopasowac automatyke do celu uzytkownika bez zmiany infrastruktury.

**Independent Test**: Mozna niezaleznie przetestowac przez uruchomienie tych samych danych wejsciowych dla kazdego trybu i weryfikacje, ze wynik odzwierciedla priorytety trybu przy niezmienionych ograniczeniach safety.

**Acceptance Scenarios**:

1. **Given** te same dane wejsciowe i konfiguracja limitow, **When** uzytkownik zmienia tryb z balanced na fast, **Then** decyzje promuja szybsze ladowanie, ale nadal respektuja limity ceny, ochrony magazynu i hard-limity techniczne.
2. **Given** te same dane wejsciowe i konfiguracja limitow, **When** uzytkownik zmienia tryb na economical, **Then** decyzje priorytetyzuja najnizszy efektywny koszt ladowania z uwzglednieniem kosztu zakupu i kosztu utraconej sprzedazy energii.
3. **Given** aktywny jest tryb manual, **When** uplywa kolejna minuta decyzyjna, **Then** system nie wykonuje automatycznych zmian sterujacych pradem ladowania.

---

### User Story 3 - Manual override i wyjasnialnosc decyzji (Priority: P3)

Jako uzytkownik chce miec pelna kontrole reczna i jasny wglad w powody decyzji automatyki, aby latwo diagnozowac zachowanie systemu i unikac konfliktu automatyki z recznym sterowaniem.

**Why this priority**: Wyjasnialnosc i respektowanie recznej kontroli sa kluczowe dla zaufania do integracji i zgodnosci z constitution.

**Independent Test**: Mozna niezaleznie przetestowac przez reczna zmiane zachowania ladowania oraz odczyt informacji diagnostycznych, bez potrzeby testowania pelnej optymalizacji kosztowej.

**Acceptance Scenarios**:

1. **Given** automatyka jest aktywna, **When** uzytkownik recznie zmieni zachowanie ladowania przez Home Assistant, EVSE lub EV, **Then** integracja przelacza sie na tryb manual i zatrzymuje automatyczne zmiany.
2. **Given** system podjal decyzje o zmianie lub utrzymaniu pradu, **When** uzytkownik sprawdza udostepnione informacje diagnostyczne, **Then** widzi aktywny tryb, kluczowe dane wejsciowe, ograniczenia oraz powod wyboru decyzji.

---

### Edge Cases

- EV jest podlaczony, ale jego SoC jest chwilowo niedostepny lub skacze do wartosci nielogicznej.
- Ceny zakupu i sprzedazy sa rowne, ujemne lub gwaltownie sie zmieniaja miedzy kolejnymi minutami.
- Dane chwilowe i srednie 5-minutowe sugeruja przeciwne kierunki zmiany pradu.
- EVSE akceptuje zadany prad, ale EV ogranicza realne ladowanie do 5 A.
- OBC jest skonfigurowany, ale nie odpowiada na polecenia lub raportuje bledny prad.
- EVSE i OBC otrzymuja polecenia, ktore w kombinacji daja efektywny prad niespojny z oczekiwaniami systemu.
- Prog zatrzymania ladowania jest przekraczany chwilowo i natychmiast przestaje byc spelniony w nastepnym cyklu decyzyjnym (flap warunku zatrzymania).
- Uzytkownik wlacza manual override dokladnie w trakcie cyklu decyzyjnego.
- Integracja uruchamia sie ponownie podczas trwajacego ladowania i musi odtworzyc bezpieczny stan bez przekroczenia limitow.
- Czesc encji raportuje dane swieze, a czesc dane przeterminowane.
- Chwilowy brak jednej ceny przyszlej w atrybutach encji cenowej przy obecnych danych biezacych.
- Import i eksport sieci wskazuja jednoczesnie wartosci niespojne z bilansem mocy.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST obslugiwac automatyczne sterowanie pradem ladowania dla jednej instalacji zawierajacej 1 EV i 1 EVSE.
- **FR-002**: System MUST pobierac dane decyzyjne wyłącznie z encji Home Assistant wskazanych przez uzytkownika.
- **FR-002a**: System MUST wydawac polecenia pradu ladowania przez zapis do encji Home Assistant (typ number lub select) steujacej EVSE, wskazanej przez uzytkownika podczas konfiguracji.
- **FR-003**: System MUST wymagac konfiguracji encji obejmujacych co najmniej: produkcje PV, SoC magazynu, moc ladowania/rozladowania magazynu, import/eksport sieci, ceny zakupu i sprzedazy, stan podlaczenia EV oraz SoC EV.
- **FR-004**: System MUST uwzgledniac ceny biezace oraz wszystkie dostepne ceny przyszle udostepnione w atrybutach encji cenowych, bez ograniczenia glebokosci horyzontu czasowego.
- **FR-004a**: System MUST byc odporny na czesciowy brak cen przyszlych w atrybutach encji cenowej: jezeli czesc rekordow cenowych jest niedostepna, system MUST podjac bezpieczna decyzje na podstawie dostepnych danych bez przerywania automatyki.
- **FR-005**: System MUST podejmowac decyzje sterujace co 1 minute.
- **FR-006**: System MUST analizowac srednie 1-minutowe i 5-minutowe przed podjeciem decyzji, aby ograniczac flapping i niepotrzebne stop/start.
- **FR-007**: System MUST wspierac tryby pracy: balanced, fast, economical, manual.
- **FR-008**: System MUST traktowac safety i predictability jako nadrzedne wobec optymalizacji we wszystkich trybach.
- **FR-009**: System MUST w trybie balanced realizowac kompromis miedzy stabilnoscia, kosztem ladowania i ochrona magazynu.
- **FR-010**: System MUST w trybie fast priorytetyzowac postep ladowania EV przy zachowaniu ograniczen hard-limit technicznych i progów SoC ochrony magazynu; limit maksymalnej mocy rozladowania magazynu (FR-023a) jest w trybie fast podwyzszony do osobno konfigurowalnej wartosci lub calkowicie wylaczony, gdy uzytkownik tak skonfiguruje.
- **FR-011**: System MUST w trybie economical priorytetyzowac minimalny efektywny koszt ladowania, liczony jako koszt zakupu energii plus koszt utraconej mozliwosci sprzedazy energii do sieci.
- **FR-012**: System MUST w trybie manual nie wykonywac automatycznych zmian sterujacych.
- **FR-013**: System MUST egzekwowac rozdzielczosc sterowania EVSE 1 A oraz zakres pracy EVSE 6-16 A.
- **FR-014**: System MUST uwzgledniac, ze ladowarka pokladowa EV (OBC) sluzy wylacznie jako dodik ograniczajacy efektywny prad ladowania. Gdy sterowanie OBC jest wlaczone (FR-026) i cel wynosi 5 A: system MUST ustawic EVSE na 6 A (jego minimum) ORAZ OBC na 5 A. Dla celow >=6 A system steruje wylacznie EVSE; OBC nie jest wowczas ograniczany poleceniem.
- **FR-015**: System MUST nigdy nie przekroczyc skonfigurowanego limitu mocy przylacza.
- **FR-016**: System MUST nie rozpoczynac automatycznego ladowania, gdy wymagane dane sa brakujace, nieaktualne, nieprawidlowe lub sprzeczne.
- **FR-016a**: System MUST uznawac wymagane dane za nieaktualne (stale), gdy czas od ostatniej aktualizacji dowolnej wymaganej encji przekracza 60 sekund.
- **FR-016b**: System MUST traktowac jednoczesnie sprzeczne dane krytyczne (np. import i eksport jednoczesnie z niespojnym bilansem) jako blad krytyczny i przejsc do fail-safe (6 A) z odpowiednim logowaniem.
- **FR-017**: System MUST, gdy ladowanie juz trwa i dane wymagane staja sie niewiarygodne, zejsc do minimalnej bezpiecznej wartosci automatycznej zamiast kontynuowac agresywna optymalizacje.
- **FR-017a**: System MUST definiowac minimalna bezpieczna wartosc automatyczna jako stale 6 A.
- **FR-018**: System MUST wykrywac manualna zmiane zachowania ladowania wykonana przez uzytkownika przez Home Assistant, EVSE lub EV oraz automatycznie przelaczac integracje do trybu manual.
- **FR-018a**: System MUST porownywac ostatnio zadany prad ladowania z rzeczywistym pradem raportowanym przez EVSE po kazdym cyklu decyzyjnym; rozbiezćnosc przekraczajaca 1 A musi byc traktowana jako sygnal manual override.
- **FR-019**: System MUST po przejsciu na tryb manual zatrzymac automatyczne korekty do czasu swiadomego powrotu uzytkownika do trybu automatycznego.
- **FR-020**: System MUST udostepniac wyjasnienie decyzji obejmujace co najmniej: aktywny tryb, kluczowe dane wejsciowe, zastosowane ograniczenia oraz powod wybranej wartosci pradu.
- **FR-021**: System MUST umozliwiac konfiguracje progow i limitow zaleznych od instalacji bez hardcodowania wartosci specyficznych dla jednej lokalizacji.
- **FR-021a**: System MUST umozliwiac konfiguracje buy_price_threshold i sell_price_threshold dla trybu economical, z domyslnymi wartosciami buy_threshold = 0 (zawsze kupuj), sell_threshold = 0 (zawsze sprzedaj).
- **FR-021b**: System MUST traktowac zmiane w sygnatach wejsciowych (moc, cena, SoC) jako uzasadniajaca przesuniencie docelowego pradu o 1 A, gdy zmiana pokrywa amplitune 1 A pradu na moc (ok. 700 W dla pradu trojfazowego).
- **FR-022**: System MUST ograniczac oscylacje pradu i unikać niepotrzebnego zatrzymywania/wznawiania ladowania, jesli nie wynika to z regul safety lub ograniczen hard-limit.
- **FR-023**: System MUST obslugiwac stopniowane progi ochrony magazynu energii oparte na SoC z trzema konfigurowalnymi przedzialami: ponizej 50% SoC, ponizej 70% SoC, ponizej 90% SoC. Progi SoC obowiazuja we wszystkich trybach automatycznych.
- **FR-023a**: Dla kazdego przedzialu SoC system MUST egzekwowac osobny, konfigurowalny limit maksymalnej mocy rozladowania magazynu wykorzystywanej do ladowania EV. W trybie fast limit ten jest zastepowany osobno konfigurowalnym limitem fast-mode lub wylaczony, gdy uzytkownik ustawi brak ograniczenia.
- **FR-023b**: Jezeli aktualne rozladowanie magazynu przekracza limit skonfigurowany dla aktywnego przedzialu SoC, system MUST ograniczyc prad ladowania EV do wartosci, ktora nie spowoduje przekroczenia tego limitu.
- **FR-024**: Po restarcie integracji system MUST odczytac aktywny tryb pracy z dedykowanej encji Home Assistant, ktora przechowuje i odtwarza wartosc po restarcie.
- **FR-024a**: Po restarcie system MUST wznowic dzialanie zgodnie z odtworzonym trybem pracy bez wymuszania trybu manual ani bez automatycznego przejscia do fail-safe, chyba ze dane encji wymaganych sa brakujace, nieaktualne lub sprzeczne zgodnie z FR-016.
- **FR-025**: System MUST preferowac redukcje pradu ladowania do najnizszej mozliwej wartosci nad calkowitym zatrzymaniem ladowania; calkowite zatrzymanie ladowania przez automatyke jest dozwolone wylacznie po przekroczeniu skonfigurowanego progu zatrzymania (FR-025a) lub w wyniku warunku fail-safe (FR-017).
- **FR-025a**: System MUST obslugiwac konfigurowalny prog zatrzymania ladowania aktywny we wszystkich trybach automatycznych, definiowany jako warunek zlych warunkow oparty na czterech niezaleznie konfigurowalnych sub-progach: (1) przekroczenie limitu mocy rozladowania magazynu, (2) przekroczenie limitu importu mocy z sieci, (3) przekroczenie limitu ceny zakupu energii z sieci, (4) spadek ceny eksportu energii do sieci ponizej skonfigurowanego minimum. Sub-progi sa laczone logika OR. Wartosci kazdego sub-progu sa konfigurowane niezaleznie dla kazdego trybu pracy (balanced, fast, economical), umozliwiajac bardziej permisywne wartosci w trybie fast.
- **FR-025b**: Prog zatrzymania ladowania (FR-025a) jest odrebny od fail-safe 6 A (FR-017a): fail-safe obejmuje problemy z jakoscia danych, natomiast prog zatrzymania obejmuje warunki ekonomiczne i ochronne. Spelnienie ktoregkolwiek sub-progu (OR) aktywuje licznik histerezy (FR-025d).
- **FR-025c**: Gdy warunki przekroczenia progu zatrzymania przestaja byc spelnione, system MUST automatycznie wznowic ladowanie w kolejnym cyklu decyzyjnym, bez wymagania manualnej akcji uzytkownika.
- **FR-025d**: System MUST egzekwowac zatrzymanie ladowania z powodu progu zatrzymania (FR-025a) dopiero po tym, jak warunek zatrzymania zostanie spelniony przez co najmniej N kolejnych cykli minutowych; N jest konfigurowalne z domyslna wartoscia 2. Wznowienie ladowania po ustaniu warunku nie wymaga dodatkowej histerezy i nastepuje w kolejnym cyklu.
- **FR-026**: System MUST obslugiwac opcjonalne sterowanie ladowarka pokladowa EV (OBC) jako drugi, konfigurowalny kanol aktuacji, uzupelniajacy sterowanie EVSE.
- **FR-026a**: Encja HA sterujaca OBC jest opcjonalna i wskazywana przez uzytkownika podczas konfiguracji; gdy nie jest skonfigurowana, system dziala w trybie EVSE-only bez utraty pozostalych funkcji.
- **FR-026b**: Gdy sterowanie OBC jest wlaczone, system MUST traktowac OBC wylacznie jako dodik ograniczajacy prad: jedyna wartosc wydawana do OBC przez automatyke wynosi 5 A i jest stosowana tylko gdy docelowy efektywny prad wynosi 5 A. W takim przypadku EVSE otrzymuje swoje minimum (6 A), a OBC ogranicza efektywny prad do 5 A. Dla wszystkich innych wartosci docelowych (>=6 A) polecenie do OBC nie jest wydawane.
- **FR-026c**: Gdy sterowanie OBC jest wlaczone, mechanizm detekcji override (FR-018a) MUST uwzglednic oczekiwany efektywny prad: jesli ostatnio wydano EVSE=6 A + OBC=5 A, oczekiwany efektywny prad wynosi 5 A; jezeli rzeczywisty prad raportowany przez EVSE lub OBC rozni sie od oczekiwanego efektywnego pradu o wiecej niz 1 A, musi byc traktowany jako sygnal manual override.
- **FR-026d**: System MUST wydawac polecenia do OBC przez zapis do encji Home Assistant wskazanej przez uzytkownika w konfiguracji, zgodnie z tym samym wzorcem co sterowanie EVSE (FR-002a).

### Non-Functional Requirements

- **NFR-001**: Decyzje sterujace musza byc deterministyczne: dla tych samych danych wejsciowych i tej samej konfiguracji wynik decyzji musi byc identyczny.
- **NFR-002**: Zachowanie systemu musi byc wyjasnialne dla uzytkownika bez potrzeby analizy kodu zrodlowego.
- **NFR-003**: Runtime musi dzialac w pelni lokalnie, bez zaleznosci od uslug chmurowych lub zdalnych silnikow decyzyjnych.
- **NFR-004**: Domyslne zachowanie musi byc konserwatywne i bezpieczne przy niepewnosci danych.
- **NFR-005**: Specyfikacja interakcji i konfiguracji musi pozostawac zgodna z Home Assistant-native patterns i oczekiwaniami jakosciowymi HACS.
- **NFR-006**: System powinien wspierac latwe debugowanie poprzez spojnosc informacji diagnostycznych miedzy kolejnymi decyzjami minutowymi.

### Acceptance Criteria

- **AC-001**: Dla poprawnej konfiguracji i kompletnych danych system wyznacza decyzje pradowa co minute dla aktywnego trybu automatycznego.
- **AC-002**: W zadnym scenariuszu testowym nie dochodzi do przekroczenia skonfigurowanego limitu mocy przylacza.
- **AC-003**: Przy wykryciu brakujacych, nieaktualnych, nieprawidlowych lub sprzecznych danych system nie rozpoczyna nowego automatycznego ladowania.
- **AC-004**: Jesli dane wymagane staja sie niewiarygodne podczas aktywnego ladowania, system redukuje sterowanie do minimalnej bezpiecznej wartosci automatycznej.
- **AC-005**: Reczna zmiana zachowania ladowania powoduje automatyczne przejscie w tryb manual i brak dalszych automatycznych zmian do czasu swiadomego wznowienia automatyki.
- **AC-006**: Dla kazdej decyzji mozna odczytac wyjasnienie obejmujace tryb, dane kluczowe, ograniczenia i powod decyzji.
- **AC-007**: W trybie manual system nie wykonuje autonomicznych zmian sterujacych niezaleznie od zmian danych wejsciowych.
- **AC-008**: W testach stabilnosci sygnalow o malej amplitudzie system unika nieuzasadnionych zmian pradu i niepotrzebnego stop/start.
- **AC-009**: W scenariuszach pogarszajacych sie warunkow (np. rosnace rozladowanie magazynu) system redukuje prad przed zatrzymaniem, a zatrzymuje ladowanie dopiero po przekroczeniu skonfigurowanego progu zatrzymania.
- **AC-010**: Po ustaniu warunkow zatrzymania system wznawia ladowanie automatycznie w kolejnym cyklu bez dodatkowej akcji uzytkownika.
- **AC-011**: Gdy sterowanie OBC jest wlaczone i skonfigurowane, system wydaje polecenia do OBC w kazdym cyklu decyzyjnym i uwzglednia prad OBC w detekcji override.

### Key Entities *(include if feature involves data)*

- **Charging Control Configuration**: Zestaw ustawien wybranych przez uzytkownika, obejmujacy mapowanie encji, limity hard, progi kosztowe i ochronne oraz aktywny tryb pracy.
- **Telemetry Snapshot**: Spójny zestaw wartosci odczytanych z wymaganych encji dla cyklu minutowego, wraz z ocena swiezosci i spojnosci danych.
- **Smoothed Metrics Window**: Wartosci srednie 1-minutowe i 5-minutowe wyliczone dla sygnalow sterujacych, wykorzystywane do stabilizacji decyzji.
- **Control Decision**: Wynik pojedynczego cyklu decyzyjnego zawierajacy docelowy prad EVSE, opcjonalne polecenie OBC, status automatyki (aktywny, ograniczony, zatrzymany, manual) oraz uzasadnienie.
- **Safety State**: Stan oceny bezpieczenstwa danych i limitow, okreslajacy czy automatyka moze zwiekszac, utrzymywac, ograniczac, zatrzymac lub wstrzymac sterowanie.
- **Stop Condition State**: Aktualny wynik ewaluacji progu zatrzymania ladowania (FR-025a), okreslajacy czy warunki uzasadniaja calkowite zatrzymanie ladowania przez automatyke.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Co najmniej 99% cykli minutowych w ciagu 7 kolejnych dni konczy sie poprawnie wyznaczona decyzja lub jawnym, bezpiecznym ograniczeniem z podanym powodem.
- **SC-002**: W 100% scenariuszy testowych i produkcyjnych nie dochodzi do przekroczenia skonfigurowanego limitu mocy przylacza.
- **SC-003**: W co najmniej 95% przypadkow manualnej interwencji system przechodzi do trybu manual w czasie do 1 cyklu decyzyjnego i nie wykonuje dalszych automatycznych zmian.
- **SC-004**: W co najmniej 95% ocenionych decyzji uzytkownik jest w stanie jednoznacznie zidentyfikowac tryb, dane kluczowe, ograniczenia i powod decyzji na podstawie dostepnych informacji diagnostycznych.
- **SC-005**: W porownaniu do stalego ladowania z maksymalnym pradem, tryb economical obniza sredni efektywny koszt energii dostarczonej do EV o co najmniej 10% w okresie referencyjnym 30 dni, bez naruszenia zasad safety.
- **SC-006**: W testach zmiennych sygnalow liczba nieuzasadnionych zmian pradu (niewynikajacych z limitow lub istotnej zmiany warunkow) nie przekracza 2 zmian na 15 minut.

## Assumptions

- Uzytkownik dysponuje stabilnie raportowanymi encjami Home Assistant wymaganymi przez zakres feature'a.
- Integracja jest wykorzystywana dla jednej instalacji EV (1 EV + 1 EVSE + 1 magazyn + 1 punkt przylacza) bez jednoczesnej obslugi wielu pojazdow.
- Minimalna bezpieczna wartosc automatyczna jest stala i wynosi 6 A.
- Domyslne progi ceny dla trybu economical sa ustawione na 0, co oznacza natychmiastowe automatyczne ladowanie bez warunku cenowego; uzytkownik moze je zmieniac poprzez konfiguracje.
- Uzytkownik swiadomie wybiera i zmienia tryb pracy, a powrot z manual do automatyki wymaga jawnej akcji uzytkownika.
- Tryb pracy jest zapisywany w encji Home Assistant, ktora automatycznie odtwarza wartosc po restarcie; integracja nie stosuje hardcodowanego trybu startowego.
- Dane cenowe przyszle moga byc okresowo niepelne; w takiej sytuacji system stosuje zachowanie bezpieczne i przewidywalne, bez nieuzasadnionego ryzyka kosztowego.
- Sterowanie OBC jest opcjonalne; gdy encja OBC nie jest skonfigurowana, system dziala poprawnie w trybie EVSE-only.
- Domyslnie prog zatrzymania ladowania nie jest ustawiony (zatrzymanie wylaczone); uzytkownik aktywuje go jawnie przez konfiguracje sub-progow.