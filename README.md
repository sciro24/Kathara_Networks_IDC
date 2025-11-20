# Internet and Data Centers – Kathara Labs

This repository contains a collection of **Kathara** lab exercises developed for the *Internet and Data Centers* course at **Roma Tre University**.  
The labs are used to practice network configuration, routing, and data center design topics covered during the course.

🚀 The repository includes **labGenerator**, a tool designed to help automatically build a complete lab environment, streamlining the creation of all its components.

[🛠️ LAB GENERATOR](#labgenerator)

---

## 📘 Partial Exam 1 – RIP/OSPF Network Configuration

This section contains the labs used to prepare for the **first midterm**, covering **RIP and OSPF routing protocols**.  
The labs focus on configuring routers, understanding basic network topologies, and practicing both single-area and multi-area OSPF scenarios.


**LABS:**

- ⚙️ [BUTTERFLY (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20BUTTERFLY%20%28OSPF%20-%20RIP%29/)
- ⚙️ [CLOUDS (OSPF MULTI-AREA)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20CLOUDS%20%28OSPF%20MULTI-AREA%29/)
- ⚙️ [FALLING ASLEEP (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20FALLING%20ASLEEP%20%28OSPF%20-%20RIP%29/)
- ⚙️ [MARACAS (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20MARACAS%20%28OSPF%20-%20RIP%29/)
- ⚙️ [PUZZLE (OSPF MULTI-AREA)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20PUZZLE%20%28OSPF%20MULTI-AREA%29/)
- ⚙️ [STREET LIGHT (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20STREET%20LIGHT%20%28OSPF%20-%20RIP%29/)
- ⚙️ [TENNIS (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20TENNIS%20%28OSPF%20-%20RIP%29/)
- ⚙️ [TWIN PAN BALANCE (OSPF - RIP)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20TWIN%20PAN%20BALANCE%20%28OSPF%20-%20RIP%29/)
- ⚙️ [UP ARROW OSPF (RIP 2 BORDER)](./Correct%20LABS/PARTIAL%20I/%E2%9C%93%20UP%20ARROW%20OSPF%20%20%28RIP%202%20BORDER%29/)




---

## 🌐 Partial Exam 2 – BGP w/ Policy

This section includes the labs used to prepare for the **second midterm**, focused on the **BGP** (Border Gateway Protocol) and routing **policy** configuration.
The exercises cover BGP setup in multi-AS environments, route filtering and preference management, and the implementation of import/export policies to control inter-domain traffic behavior.


**LABS:**
- ⚙️ [CANDY (BGP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20CANDY%20%28BGP%29/)
- ⚙️ [DESCONOCIDA (BGP - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20DESCONOCIDA%20%28BGP%20-%20RIP%29/)
- ⚙️ [GALAXY (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20GALAXY%20%28BGP%20-%20OSPF%20-%20RIP%29/)
- ⚙️ [INCOGNITA (BGP - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20INCOGNITA%20%28BGP%20-%20RIP%29/)
- ⚙️ [PEAR TO PEAR (BGP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20PEAR%20TO%20PEAR%20%28BGP%29/)
- ⚙️ [RED BARON (BGP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20RED%20BARON%20%28BGP%29/)
- ⚙️ [T1-C2 (BGP - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20T1-C2%20%28BGP%20-%20RIP%29/)
- ⚙️ [T2-C1 (BGP - OSPF)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20T2-C1%20%28BGP%20-%20OSPF%29/)
- ⚙️ [TROUSERS (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20TROUSERS%20%28BGP%20-%20OSPF%20-%20RIP%29/)
- ⚙️ [HOUR GLASS (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20HOUR%20GLASS%20%28BGP%20-%20OSPF%20-%20RIP%29/)
- ⚙️ [PAPILLON (BGP - OSPF - RIP)](./Correct%20LABS/PARTIAL%20II/%E2%9C%93%20PAPILLON%20%28BGP%20-%20OSPF%20-%20RIP%29/)




---

## 🧩 Partial Exam 3 – DNS

This section includes the labs used to prepare for the **third midterm**, focused on **BGP**, **IGP** (OSPF/RIP), and **DNS** configuration.
The exercises cover multi-protocol routing setup, inter-domain and intra-domain traffic management, and the deployment and troubleshooting of DNS services in a networked environment.


**LABS:**
- ⚙️










---

## ☁️ Partial Exam 4 – 









---

# LabGenerator

## 📋 Descrizione

`labGenerator.py` è uno strumento Python interattivo progettato per automatizzare la creazione di laboratori Kathara per l'emulazione di reti complesse. Il tool semplifica notevolmente il processo di configurazione di router, host, server web e server DNS, generando automaticamente tutti i file di configurazione necessari per i protocolli di routing (BGP, OSPF, RIP) tramite FRRouting (FRR).

## ✨ Funzionalità Principali

### 🔧 Modalità di Funzionamento

Il generatore supporta diverse modalità operative:

1. **Creazione Interattiva** - Crea un nuovo laboratorio passo-passo con assistenza guidata
2. **Importazione da File** - Importa configurazioni esistenti da file XML/JSON
3. **Rigenerazione XML** - Ricostruisce il file XML di metadati da un lab esistente
4. **Generazione Comandi PING** - Crea automaticamente comandi ping per testare la connettività tra tutti i dispositivi
5. **Configurazione DNS** - Assegna file `resolv.conf` personalizzati ai dispositivi
6. **Gestione Loopback** - Aggiunge interfacce loopback a dispositivi esistenti
7. **Policy BGP** - Applica policy BGP avanzate (access-list, prefix-list, route-map, customer-provider)

### 📦 Componenti Supportati

- **Router FRR**: Configurazione automatica di router con supporto per:
  - BGP (Border Gateway Protocol)
  - OSPF (Open Shortest Path First) - single-area e multi-area
  - RIP (Routing Information Protocol)
  - Routing statico
  - Aggregazione automatica delle reti
  - Policy BGP avanzate
  
- **Host**: Dispositivi endpoint con configurazione IP e gateway
  - Supporto interfacce multiple
  - Route statiche personalizzabili

- **Server WWW**: Server Apache con pagine HTML personalizzate
  - Generazione automatica di `index.html`
  - Configurazione IP e routing

- **Server DNS (BIND9)**: Server DNS con supporto completo
  - Root server o recursive resolver
  - Zone authoritative personalizzate
  - Forwarders configurabili
  - Record A, NS, CNAME, PTR

## 🚀 Uso del Tool

### Prerequisiti

- Python 3.x
- Kathara installato
- Docker installato

### Avvio

```bash
python3 labGenerator.py
```

### Menu Principale

Quando si avvia in modalità interattiva, il tool presenta le seguenti opzioni:

```
C - Crea nuovo laboratorio (interattivo)
I - Importa da file (XML/JSON)
R - Rigenera XML di un lab esistente
G - Genera comando PING per un lab esistente
A - Assegna un file resolv.conf specifico a un dispositivo
L - Aggiungi loopback a dispositivo in un lab esistente
P - Applica Policies BGP
Q - Esci
```


---

---

### 🏫 Author
**Diego** – Computer Engineering student at *Roma Tre University*  
*Born from an idea by Rainer Cabral Ilao*

