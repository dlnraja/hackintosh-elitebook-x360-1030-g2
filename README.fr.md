# HP EliteBook x360 1030 G2 — OpenCore

Configuration OpenCore reproductible pour l'HP EliteBook x360 1030 G2 (Kaby Lake, 2017). Les scripts téléchargent des versions épinglées, compilent les sources ACPI de ce dépôt et assemblent `dist/EFI`. Aucun binaire OpenCore ou kext n'est commité.

Ce dépôt **n'a pas été démarré** sur un 1030 G2. Le tableau plus bas sépare ce qui a été vérifié de ce qui reste un rapport communautaire ou un point non testé.

La licence de macOS vise le matériel Apple. L'usage que vous en faites vous appartient.

[English guide](README.md)

## Quelle version de macOS

**Installez macOS Sequoia 15.2 ou plus récent.** C'est la version récente qui a encore un chemin court et documenté pour ce processeur.

Tahoe n'est pas le chemin simple :

- Le guide Dortania pour portable Kaby Lake associe cette classe de machine au SMBIOS `MacBookPro14,1` (13 pouces, double cœur, 15 W, sans Touch ID). Apple a retiré ce modèle avec Sonoma. La liste des modèles d'OpenCore Legacy Patcher l'inclut encore et marque les graphismes comme natifs. La page post-installation d'OCLP, lue le 2026-10-26, ne cite les iGPU Intel à root-patcher sous Sequoia que jusqu'à Skylake. Kaby Lake n'y figure pas. Un root patch est donc peut-être inutile. Ce portable n'a pas servi à le confirmer.
- OCLP 2.5.1 (19 septembre 2026) est la version stable et prend Sequoia en charge. OCLP 3.0.0-rc.3 (8 octobre 2026) est une préversion pour macOS Tahoe. La page Tahoe de Dortania ne liste que quatre familles de SMBIOS encore prises en charge par Apple, toutes plus récentes que Kaby Lake, et elle indique qu'AppleHDA a été retiré : AppleALC ne peut plus piloter un codec Conexant sous Tahoe. Le suivi reste dans les tickets [#1167](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1167) et [#1183](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1183). Ce dernier dit que le projet s'arrête à Tahoe et ne vise pas macOS 27.
- `AirportItlwm` officiel 2.3.0 s'arrête à Sonoma. Les builds Sequoia et Tahoe de l'EFI par défaut viennent de [laobamac/itlwm](https://github.com/laobamac/itlwm) `v2.4.0-alpha` (commit `738d4c6`, 11 octobre 2026). Cette publication demande encore une validation matérielle. Le kext Sequoia vise Darwin 24.2 et suivants (macOS 15.2+). `itlwm.kext` officiel 2.3.0 est présent et **désactivé**. Il passe par l'application HeliPort, et ses notes de version s'arrêtent à Sonoma.

Un message MacRumors vers le 25 octobre 2026 affirme qu'un HD 620/630 peut démarrer Tahoe 26.7.1 sans root patch sur un autre EliteBook. Ce n'est pas un essai du 1030 G2, ni une promesse d'OCLP. Pour un essai Tahoe : le kext Airport Tahoe est déjà dans l'EFI et ne se charge que sous Darwin 25, l'audio analogique doit être considéré comme cassé, et `-ibtcompatbeta` n'est **pas** dans les arguments par défaut (Dortania le demande pour le Bluetooth Intel sous macOS 26).

## Matériel visé

D'après les QuickSpecs HP de l'EliteBook x360 1030 G2, document mondial c05275190, DA 15726, version 17 (4 juin 2019), la fiche EMEA et la page HP Japon là où la carte Wi-Fi est nommée :

| Élément | Description HP |
| --- | --- |
| Processeur | i5-7200U, i5-7300U ou i7-7600U. Tous sont des Kaby Lake double cœur avec HD Graphics 620. |
| Mémoire | DDR4-2133 soudée, 4 / 8 / 16 Go. Non accessible. |
| Écran | Tactile 13,3 pouces FHD ou UHD, ou FHD avec HP Sure View. La dalle UHD n'a pas été essayée avec ce framebuffer. |
| Sans fil | Intel 802.11ac 2x2 et Bluetooth 4.2. La fiche EMEA et la page japonaise nomment l'Intel Wireless-AC 8265. OpenIntelWireless liste cette carte. |
| Ports | 1 USB-C avec Thunderbolt, 2 USB 3.1 Gen 1 (dont un à charge), HDMI 1.4, alimentation cylindrique, prise combo, micro-SIM externe, microSD, lecteur de carte à puce. |
| Audio | Bang & Olufsen, quatre haut-parleurs, deux microphones. Le codec n'est **pas** dans les QuickSpecs. |
| Pavé | Clickpad en verre. HP ne nomme ni Synaptics, ni ELAN, ni Alps. |
| Autre | Webcam 720p et caméra IR, capteur d'empreinte, stylet HP Active Pen Wacom en option, WWAN et NFC en option. |

Certains dépôts GitHub parlent de LPDDR3, de deux ports USB-C ou d'un clickpad AlpsAlpine V8. Cela contredit les QuickSpecs (un USB-C, DDR4) ou n'y figure pas (vendeur du clickpad). Comptez les ports sur votre machine.

## Vérifié et non vérifié

| Affirmation | État |
| --- | --- |
| `config/config.plist` suit le Sample.plist d'OpenCore 1.0.8 | Fait par le script |
| Les sources ACPI compilent avec iasl, 0 avertissement | Fait localement avec iasl 20230628 |
| Les URL correspondent aux publications de `versions.env`, empreintes dans `scripts/checksums.sha256` | Fait par le script |
| Série, MLB, UUID et ROM restent des placeholders dans git | Imposé par le script |
| `ocvalidate` d'OpenCore 1.0.8 | Exécuté par `.github/workflows/efi.yml` sur `macos-latest`. Le binaire est Mach-O : un poste Linux l'ignore, sauf avec `--require-ocvalidate`. |
| Démarrage, veille, charge, dalle | **Non testé** |
| Wi-Fi, Bluetooth, audio, trackpad, tactile, stylet, microSD, Thunderbolt, webcam, pourcentage de batterie | **Non testé** |

### Rapports communautaires (non rejoués ici)

| Sujet | Ce qui a été écrit | Où |
| --- | --- | --- |
| Sequoia sur un 1030 G2 i5-7200U | Succès. Le premier texte dit que tout marche sauf AirDrop, tactile coupé dans le BIOS, Wi-Fi « avec ITLWM ». | [r/hackintosh_life](https://www.reddit.com/r/hackintosh_life/comments/1p1dctt/success_hp_elitebook_x360_1030_g2_on_macos_sequoia/), [r/hackintosh](https://www.reddit.com/r/hackintosh/comments/1p8b01q/success_hp_elitebook_x360_1030_g2_on_macos_sequoia/) |
| EFI du même auteur | Sequoia, Wi-Fi avec Handoff et AirPlay, Bluetooth après la veille, haut-parleurs, gestes du trackpad, USB-C, lecteur de carte, batterie, veille. Empreinte non prise en charge. Le tactile est à la fois « OK » et « non testé ». SMBIOS demandé : `MacBookPro16,2`, que ce dépôt **n'utilise pas**. | [Fudo7sei/HP-Elitebook-1030-G2-X360-Hackingtosh-EFI](https://github.com/Fudo7sei/HP-Elitebook-1030-G2-X360-Hackingtosh-EFI) |
| Tentative précédente | Boucle de redémarrage Sequoia avec `MacBookPro15,2`, alors que Ventura marchait en `MacBookPro14,1`. | [Fil Olarila](https://olarila.com/topic/44175-hp-elitebook-x360-1030-g2-possible-to-install-sequoia-on-it/) |
| EFI Ventura / Sonoma | `MacBookPro14,1`, layout audio 21, Alps V8, Intel 8265. AirDrop présenté comme dépendant d'une carte Broadcom. Empreinte non prise en charge. | [RealSameerAlSahab/HP-Elitebook-X360-1030-G2-Hackingtosh-EFI](https://github.com/realsameeralsahab/hp-elitebook-x360-1030-g2-hackingtosh-efi) |
| Layout audio | Layouts AppleALC du CX8200 : 3, 15, 21, 23 et 80. Le 21 a été ajouté pour un HP Spectre, le 23 pour un ProBook 440 G5. Aucune note ne cite le 1030 G2. | [AppleALC CX8200](https://github.com/acidanthera/AppleALC/blob/master/Resources/CX8200/Info.plist) |

Machines proches, **pas** des EFI interchangeables : x360 1030 G3 et EliteBook 830 G4/G5 (souvent Whiskey Lake, cartes différentes). Voir [EliaAmir/hackintosh-elitebook-x360-1030-g3](https://github.com/EliaAmir/hackintosh-elitebook-x360-1030-g3), [yingw/HP-Elitebook-X360-1030-G3-Hackintosh](https://github.com/yingw/HP-Elitebook-X360-1030-G3-Hackintosh), [BourneKoloh/HP-Elitebook-x360-OC-EFI](https://github.com/BourneKoloh/HP-Elitebook-x360-OC-EFI), [jkaninda/Hackintosh-HP-EliteBook-830-G5-OC-Ventura](https://github.com/jkaninda/Hackintosh-HP-EliteBook-830-G5-OC-Ventura), [ebuyzone/Hackintosh-HP-Elitebook-830-G5](https://github.com/ebuyzone/Hackintosh-HP-Elitebook-830-G5), [nguyenthienhoan/HP-EliteBook-830-G5-OpenCore](https://github.com/nguyenthienhoan/HP-EliteBook-830-G5-OpenCore). Aucun dépôt 830 G4 entretenu n'est sorti de cette recherche.

Empreinte digitale : tous les retours trouvés sur ce modèle disent qu'elle ne marche pas, et cet EFI n'a pas de kext pour elle. Non retesté ici.

## Construire l'EFI

Il faut Python 3, `iasl` (paquet `acpica-tools`, ou `brew install acpica`) et un accès réseau au premier lancement. Les archives vont dans `cache/` et sont contrôlées avec `scripts/checksums.sha256`.

Linux ou macOS :

```bash
bash scripts/build-efi.sh
```

Windows PowerShell :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-efi.ps1
```

| Option | Effet |
| --- | --- |
| `--wifi sequoia` | Défaut. AirportItlwm Sequoia actif sur Darwin 24.2–24.99, AirportItlwm Tahoe actif sur Darwin 25, `itlwm.kext` présent mais éteint. |
| `--wifi itlwm` | `itlwm` officiel 2.3.0 allumé, les deux Airport éteints. Installez [HeliPort](https://github.com/OpenIntelWireless/HeliPort) ensuite. Le Recovery n'aura pas de menu Wi-Fi. |
| `--wifi sonoma` | AirportItlwm officiel 2.3.0 pour Sonoma 14.0 et 14.4, filtrés par version de noyau. |
| `--wifi ventura` | AirportItlwm officiel 2.3.0 Ventura. |
| `--wifi all` | Toutes ces variantes Airport. Une seule plage de noyau se charge. `itlwm` reste éteint. |
| `--alcid 23` | Layout de départ. Le défaut 21 n'est qu'un point de départ communautaire. |
| `--with-cpufriend` | Télécharge aussi CPUFriend 1.3.0. Il reste éteint tant que `user/CPUFriendDataProvider.kext` n'existe pas. |

L'archive est `dist/EliteBook-x360-1030-G2-OpenCore.zip`. Copiez le dossier `EFI` qu'elle contient sur la partition EFI de la clé. `config/config.plist` dans git est le modèle à placeholders. Le fichier à démarrer est `dist/EFI/OC/config.plist`.

N'activez jamais `itlwm.kext` en même temps qu'un `AirportItlwm*.kext`. OpenIntelWireless indique que les deux se cassent mutuellement.

### Versions

| Composant | Version |
| --- | --- |
| OpenCore | 1.0.8 |
| Lilu | 1.7.2 |
| VirtualSMC | 1.3.8 |
| WhateverGreen | 1.7.1 |
| AppleALC | 1.9.8 |
| RestrictEvents | 1.1.6 |
| NVMeFix | 1.1.3 |
| HibernationFixup | 1.5.4 |
| BrightnessKeys | 1.0.3 |
| VoodooPS2 | 2.3.7 (plugin clavier actif ; souris, trackpad et son VoodooInput présents mais éteints) |
| VoodooI2C | 2.9.1 (satellite HID allumé ; Synaptics, ELAN, Atmel et FTE présents et éteints) |
| ECEnabler | 1.0.6 |
| IntelBluetoothFirmware | 2.4.0, plus BlueToolFixup de BrcmPatchRAM 2.7.2 |
| itlwm / AirportItlwm officiel | 2.3.0 |
| AirportItlwm laobamac | v2.4.0-alpha Sequoia et Tahoe |
| RealtekCardReader + Friend | 0.9.7 et 1.0.4 |
| Kext USBToolBox | 1.2.0, éteint tant qu'il n'y a pas de carte USB |
| CPUFriend | 1.3.0, seulement sur demande |
| OCLP, si besoin | 2.5.1 pour Sequoia. 3.0.0-rc.3 est une préversion réservée à Tahoe. |

`IntelBluetoothInjector.kext` n'est pas copié. OpenIntelWireless demande `IntelBluetoothFirmware` + `IntelBTPatcher` + `BlueToolFixup`, pas l'injecteur.

La page de compatibilité Bluetooth d'OpenIntelWireless liste des identifiants USB dont `0x8087:0x0a2a` et `0x0a2b`. Ce dépôt n'a pas lu l'identifiant sur un 1030 G2. Vérifiez-le dans le Gestionnaire de périphériques si le Bluetooth n'apparaît pas.

## SMBIOS

Le produit est `MacBookPro14,1`, le choix Dortania pour cette classe de CPU. `RestrictEvents` est actif avec `revpatch=sbvmm` : le README du kext décrit ce correctif comme le moyen d'obtenir les mises à jour pour un board-id non pris en charge à partir de macOS 11.3. `SecureBootModel` vaut `Disabled`, parce que les notes Dortania pour les mises à jour à partir de macOS 14.4 demandent de le couper quand `sbvmm` est utilisé. Que cette combinaison fasse vraiment démarrer l'installeur Sequoia sur ce portable est **non testé**.

Générez une identité sur la machine qui construit l'EFI. Le script appelle `macserial` des utilitaires OpenCore 1.0.8, le même binaire que télécharge [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) :

```bash
bash scripts/generate-smbios.sh
bash scripts/build-efi.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts\generate-smbios.ps1
powershell -ExecutionPolicy Bypass -File scripts\build-efi.ps1
```

`user/smbios.json` est ignoré par git. Contrôlez le numéro sur la page de couverture Apple : le résultat attendu est « introuvable », pas la fiche d'un vrai Mac. Ne commitez pas ce fichier, ne le collez pas dans un ticket, et ne réutilisez pas le numéro de quelqu'un d'autre.

`ROM` contient six octets aléatoires. Après l'installation, vous pouvez le remplacer par l'adresse MAC de la 8265 si le réglage iMessage le demande. iMessage lui-même n'est pas testé.

## BIOS

Chez HP, **F10** ouvre la configuration et **F9** le menu de démarrage. Les noms de menus changent d'une révision à l'autre. Suivez l'intention, pas un chemin de menu inventé.

D'après la page portable Kaby Lake de Dortania, adaptée à un firmware HP qui cache beaucoup de ces options :

- Coupez Secure Boot, Legacy / CSM et Fast Boot.
- Coupez TPM / Intel Platform Trust et Intel SGX si les entrées existent.
- Laissez VT-x **activé**. Coupez VT-d, ou laissez-le : `DisableIoMapper` est déjà vrai.
- Si une entrée de mémoire vidéo ou DVMT existe, mettez **64 Mo ou plus**. Les notes communautaires du 1030 G2 disent que l'option est là et qu'elles utilisent 64 Mo. Les QuickSpecs ne documentent pas le menu. Si vous ne la trouvez pas et qu'un panic graphique apparaît, voyez le dépannage (mémoire stolen). Ces propriétés ne sont pas actives par défaut.
- Il n'y a en général **pas** d'interrupteur CFG Lock. `AppleXcpmCfgLock` est donc vrai. `ControlMsrE2.efi` est dans le sélecteur (touche espace) pour lire le MSR 0xE2.
- Laissez le sans-fil actif, et le tactile si vous voulez l'essayer.
- Pour la première installation, réglez la sécurité Thunderbolt sur l'option qui ne bloque pas l'USB-C. Dortania propose de couper complètement le Thunderbolt si l'installeur se fige, puis de le rouvrir. Cet EFI **n'a pas** de SSDT de hotplug Thunderbolt. Les données USB-C peuvent passer sans. Les périphériques Thunderbolt et la station HP ne sont pas testés.
- `UnblockFsConnect` et `LapicKernelPanic` sont vrais parce que Dortania les signale pour HP.

Les listes BIOS communautaires (Fudo7sei, RealSameerAlSahab) parlent aussi de couper l'économie d'énergie de la carte à puce HP et de laisser Fast Charge au choix. Ces libellés n'ont pas été vérifiés dans un manuel HP de ce modèle. Ignorez-les s'ils n'apparaissent pas.

## Clé d'installation depuis Windows

Faites-le une fois l'EFI construit. Mappez l'USB **avant** l'installation si vous le pouvez. `XhciPortLimit` est coupé parce qu'il n'est plus fiable depuis macOS 11.3, et Sequoia est bien au-delà. Au-delà de 15 ports sur un contrôleur, la clé peut disparaître au second redémarrage. Le nombre de ports de cette machine n'a pas été relevé.

### Carte USB (recommandé d'abord)

1. Sous Windows, téléchargez l'**outil** USBToolBox depuis [USBToolBox/tool](https://github.com/USBToolBox/tool). Le kext épinglé ici est 1.2.0 ; l'outil Windows est un autre dépôt et n'est pas inclus.
2. Lancez-le, choisissez le contrôleur xHCI et exportez `UTBMap.kext`.
3. Placez ce bundle dans `user/UTBMap.kext` et relancez la construction. Le script active alors `USBToolBox.kext` et la carte.

### Image de recovery (méthode Windows de Dortania)

Utilisez `macrecovery.py` depuis l'archive OpenCore 1.0.8 déjà en cache (`cache/src/OpenCore/Utilities/macrecovery/`) ou depuis la [publication OpenCore 1.0.8](https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8).

```bat
py macrecovery.py -b Mac-937A206F2EE63C01 -m 00000000000000000 -os default download
```

Dans cette publication OpenCore, `boards.json` associe `Mac-937A206F2EE63C01` à **15.8**. Cet identifiant ne sert qu'à télécharger l'image. Ce n'est pas le SMBIOS de cet EFI. Lisez la sortie du script. Si la version est 15.x, continuez. Si c'est 26.x, vous avez Tahoe : arrêtez et prenez Sequoia avec gibMacOS. `-os latest` suit plus volontiers le catalogue le plus récent d'Apple ; laissez `default`.

Formatez une clé en FAT32 (Gestion des disques, ou Rufus en grand FAT32 non amorçable si la clé dépasse 32 Go). Créez `com.apple.recovery.boot` et copiez-y le `.dmg` et le `.chunklist`. Copiez `dist/EFI` à la racine de la même clé, à côté de `com.apple.recovery.boot`.

L'installeur de recovery télécharge le reste de macOS. `AirportItlwm` peut afficher le menu Wi-Fi dans le Recovery. `itlwm` ne le peut pas, sauf Ethernet USB ou partage de connexion.

### Installeur hors ligne (gibMacOS)

1. Clonez [corpnewt/gibMacOS](https://github.com/corpnewt/gibMacOS) et lancez `gibMacOS.bat`.
2. Choisissez une entrée **Sequoia 15.2 ou plus récente**, pas Tahoe.
3. Construisez la clé avec la commande que gibMacOS affiche (`MakeInstall.bat` ou l'équivalent, selon la révision clonée).
4. Montez la partition EFI de cette clé et copiez-y `dist/EFI`.

## Installation

1. F9, choisissez la clé.
2. Le sélecteur texte d'OpenCore s'affiche. Espace montre Reset NVRAM, Toggle SIP, le shell et l'outil CFG Lock.
3. Démarrez l'installeur. L'affichage verbeux (`-v`) est voulu.
4. Utilitaire de disque : effacez la cible en APFS, table GUID. Ne débranchez Windows que si c'est le but.
5. Installez, et laissez chaque redémarrage repartir de la clé tant que le volume interne ne démarre pas seul.
6. Montez l'EFI interne et copiez-y le même dossier `EFI`. Gardez la clé tant que l'EFI interne n'a pas démarré deux fois.

L'affichage peut rester lent ou en basse résolution au début. Ne « corrigez » pas cela en passant le SMBIOS à `MacBookPro16,2` pendant l'installation. C'est ce que demande l'EFI Fudo7sei. Ce dépôt reste sur `MacBookPro14,1` pour coller au Mac Kaby Lake qu'OCLP connaît. Changer de SMBIOS n'a pas été testé ici et peut faire ignorer le chemin Kaby Lake à un patcher.

## Après l'installation

### Graphismes et OCLP

Démarrez une fois et ouvrez À propos de ce Mac. Si le GPU annonce une taille de mémoire de framebuffer normale et que la barre des menus est translucide, laissez OCLP de côté.

Si l'interface est en rendu logiciel, téléchargez **OCLP 2.5.1** depuis les [publications Dortania](https://github.com/dortania/OpenCore-Legacy-Patcher/releases/tag/2.5.1) et lancez le root patch post-installation. La page d'OCLP peut dire que ce modèle n'a pas besoin de correctif graphique. Croyez l'application. Si elle patche, elle indique aussi la valeur SIP qu'elle veut. Notre `csr-active-config` est `00000000` (SIP actif). Ne le changez que pour la valeur affichée par OCLP, puis reconstruisez ou éditez la config démarrée et videz la NVRAM. Les root patchs sont effacés par les mises à jour de macOS et doivent être refaits. C'est décrit par OCLP et ce n'est pas rejoué ici.

N'installez pas OCLP 3.0.0-rc.3 sauf pour un essai Tahoe avec une sauvegarde.

### Audio

`alcid=21` est l'argument par défaut. C'est le layout cité par les EFI communautaires de ce portable, et aussi un layout CX8200 écrit par AppleALC pour un autre HP. Sans son :

1. Identifiez le codec sous Windows. Si ce n'est pas un Conexant CX8200, ne piochez pas dans la liste qui suit.
2. Si c'est un CX8200, essayez `alcid=23`, puis `15`, `3` et `80`, un seul à la fois, avec un reset NVRAM entre chaque essai.
3. Sous Tahoe, arrêtez. AppleHDA n'est plus là, AppleALC ne ramènera pas les haut-parleurs. Les pistes Dortania sont un root patch qui remet AppleHDA, ou VoodooHDA avec une qualité moindre. Aucun des deux n'est branché dans cet EFI, et aucun n'est testé.

### Changer de version Wi-Fi

L'EFI par défaut filtre déjà AirportItlwm Sequoia et Tahoe par version de noyau. Passer d'un OS à l'autre ne demande pas de reconstruction. Pour l'`itlwm` officiel :

```bash
bash scripts/build-efi.sh --wifi itlwm
```

Installez ensuite HeliPort. AirDrop sur la 8265 est signalé comme absent par le premier texte Reddit et par le README RealSameer. Le README Fudo7sei parle plus tard de Handoff et d'AirPlay. Rien de cela n'a été contrôlé ici.

### Carte USB, si vous l'avez sautée

Les mêmes étapes USBToolBox que plus haut. Hackintool sous macOS est l'autre chemin courant ; ce guide ne le détaille pas, parce que la carte faite sous Windows est celle que Dortania recommande une fois `XhciPortLimit` coupé.

### CPUFriend

Facultatif. XCPM natif plus `SSDT-PLUG` est la base Dortania pour Kaby Lake, et c'est ce que cet EFI livre. Un fournisseur de données CPUFriend peut affiner le profil. Il n'est pas inclus : un vecteur de fréquences copié d'une autre machine serait une supposition.

1. Installez [CPUFriendFriend](https://github.com/corpnewt/CPUFriendFriend) sur le système démarré.
2. Générez un kext fournisseur pour `MacBookPro14,1`.
3. Placez-le dans `user/CPUFriendDataProvider.kext`.
4. Lancez `bash scripts/build-efi.sh --with-cpufriend` et copiez le nouvel EFI.

### Trackpad, tactile, stylet

`VoodooI2CHID` est le satellite actif : il couvre beaucoup de pavés HID-over-I2C, dont certains Alps et ELAN. `VoodooI2CSynaptics` et `VoodooI2CELAN` sont dans l'EFI et éteints. N'en activez un qu'après avoir éteint HID, et seulement une fois le vendeur connu sous Windows. Les plugins souris et trackpad PS/2 sont présents et éteints, pour ne pas entrer en conflit avec l'I2C. Le plugin clavier reste actif.

`SSDT-GPIO` met `GPEN` / `SBRG` à 1 et `GPHD` à 0 quand ces objets existent. C'est un schéma Kaby Lake générique, pas un extrait du DSDT de cette carte. Si le pavé reste mort, désactivez `SSDT-GPIO`, activez `SSDT-XOSI` **et** le renommage `_OSI` vers `XOSI` ensemble, puis redémarrez. `XOSI` répond oui à `Darwin` pour que les autres SSDT gardent leurs tests macOS. Laissez le renommage éteint tant que vous n'en avez pas besoin : OpenCore l'applique aussi quand Windows démarre via OpenCore.

Le tactile et le stylet optionnel ne sont pas testés. Un README communautaire liste le tactile à la fois comme fonctionnel et comme non testé. HP décrit le stylet comme une pièce Wacom optionnelle.

### Batterie, luminosité, lecteur de carte

`ECEnabler` plus `SMCBatteryManager` est le moyen habituel de lire un contrôleur embarqué dont les champs dépassent un octet, sans SSDT batterie écrit à la main. `SSDT-EC` ajoute un faux appareil `ACID0001` pour qu'AppleBusPower trouve un objet nommé EC, sans prendre le vrai `PNP0C09`. Si le journal dit `AE_ALREADY_EXISTS` pour `EC`, désactivez seulement `SSDT-EC`.

`SSDT-PNLF` publie un appareil de rétroéclairage avec `_UID` 16, le profil Skylake/Kaby Lake de WhateverGreen. `BrightnessKeys` est actif pour les touches F. Les deux sont non testés. Les QuickSpecs donnent F2/F3 pour la luminosité et F5–F7 pour le volume.

`RealtekCardReader` et `RealtekCardReaderFriend` sont actifs parce que le lecteur est décrit comme Realtek dans des notes communautaires et dans la demande à l'origine de ce dépôt. Les QuickSpecs HP disent seulement « microSD ». Si l'identifiant PCI n'est pas pris en charge par le kext, le lecteur restera vide. Vérifiez l'identifiant avant d'ouvrir un ticket sur le kext.

## Dépannage

| Ce que vous voyez | Premier essai |
| --- | --- |
| Panic noyau qui cite LAPIC | `LapicKernelPanic` doit déjà être vrai. Si vous l'avez coupé, remettez-le. |
| Le sélecteur ne montre pas le disque interne | `UnblockFsConnect` et `ScanPolicy` 0 sont déjà réglés. Videz la NVRAM depuis le sélecteur. |
| `OCB: LoadImage failed - Security violation` | `SecureBootModel` doit déjà valoir `Disabled`. Secure Boot doit aussi être coupé dans le BIOS. |
| Boucle de redémarrage juste après le sélecteur | Démarrez en verbeux et lisez les dernières lignes. Depuis 11.3, une carte USB absente ou fausse fait cela. `XhciPortLimit` ne vous sauvera pas sous Sequoia. |
| Écran noir ou panic avant le bureau, et DVMT impossible à régler | Sous `PciRoot(0x0)/Pci(0x2,0x0)`, ajoutez `framebuffer-patch-enable` = `01000000`, `framebuffer-stolenmem` = `00003001`, `framebuffer-fbmem` = `00009000`. Dortania documente cela pour 32 Mo de mémoire stolen. Retirez-les si 64 Mo marche déjà. |
| Image, mais pas d'accélération | Essayez l'identifiant `00001659` à la place de `00001B59` (l'alternative Dortania pour le HD 620). Ensuite OCLP 2.5.1. N'empilez pas des correctifs de connecteur « au cas où ». |
| HDMI qui fige quand un écran est branché | La page portable Kaby Lake de Dortania a deux jeux de correctifs con1/con2. Un seul jeu à la fois. L'HDMI de ce châssis n'est pas testé : ne les activez pas d'avance. |
| Pas d'audio | Voir la section audio. Sous Tahoe, AppleALC ne peut pas gagner. |
| Pas de Wi-Fi sous Sequoia 15.0 ou 15.1 | Le kext Sequoia de laobamac commence à 15.2. Mettez macOS à jour ou passez à `--wifi itlwm`. |
| Pas de Wi-Fi sous Tahoe | Vérifiez que `AirportItlwm_Tahoe` est bien le kext chargé, et lisez les notes laobamac : alpha, WPA3 seul et AirDrop non pris en charge. |
| Pas de Bluetooth sous Tahoe | Ajoutez l'argument `-ibtcompatbeta`. Ne l'ajoutez pas sous Sequoia tant que vous n'en avez pas besoin. |
| Trackpad mort | Vendeur, puis bascule HID / Synaptics / ELAN, puis GPIO contre XOSI. |
| La CMOS se remet à zéro ou la machine tombe en mode sans échec après extinction | Mettez `DisableRtcChecksum` à vrai. Il est livré à faux. |
| Windows se comporte mal quand il est lancé depuis OpenCore | Les SSDT sont conditionnés par Darwin. Le renommage `_OSI` ne l'est pas. Laissez ce renommage éteint. |

## Arborescence

```
acpi/                 Sources SSDT. Le script les compile.
config/config.plist   Modèle à placeholders, produit depuis Sample.plist.
scripts/efi_build.py  Téléchargement, compilation et écriture de la config.
scripts/build-efi.sh  Point d'entrée Linux et macOS.
scripts/build-efi.ps1 Point d'entrée Windows.
scripts/generate-smbios.sh / .ps1
scripts/checksums.sha256
versions.env
user/                 Fichier SMBIOS ignoré par git, et kexts optionnels.
dist/                 Sortie de construction, non commitée.
```

## Sources

Réécrit à partir de ces pages. Rien n'est recopié en bloc.

- QuickSpecs HP, EliteBook x360 1030 G2, c05275190, DA 15726, version 17, 4 juin 2019, et la [fiche EMEA](https://ck-group.lu/wp-content/uploads/2018/03/Documentation-anglais-elitebook-X360-1030-G2.pdf) qui nomme la 8265 et les trois processeurs. La [page HP Japon](https://jp.ext.hp.com/notebooks/business/elitebook_x360_merit/) nomme aussi la 8265.
- [Dortania, portable Kaby Lake](https://dortania.github.io/OpenCore-Install-Guide/config-laptop.plist/kaby-lake.html) pour le SMBIOS, les quirks, l'identifiant `00001B59`, la liste de SSDT, et les rappels HP `LapicKernelPanic` / `UnblockFsConnect`.
- [Dortania, installeur Windows](https://dortania.github.io/OpenCore-Install-Guide/installer-guide/windows-install.html) et `Utilities/macrecovery` d'OpenCore 1.0.8.
- [Dortania, contrôleur embarqué](https://dortania.github.io/Getting-Started-With-ACPI/Universal/ec-fix.html) et les exemples OpenCore `SSDT-EC-USBX` / `SSDT-PLUG`.
- [Dortania, notes macOS Tahoe](https://dortania.github.io/OpenCore-Install-Guide/extras/tahoe.html) pour le retrait d'AppleHDA, la liste de SMBIOS natifs et `-ibtcompatbeta`.
- [Modèles OCLP](https://dortania.github.io/OpenCore-Legacy-Patcher/MODELS.html), [retrait Sonoma](https://dortania.github.io/OpenCore-Legacy-Patcher/SONOMA-DROP.html), [retrait Sequoia](https://dortania.github.io/OpenCore-Legacy-Patcher/SEQUOIA-DROP.html) et [post-installation](https://dortania.github.io/OpenCore-Legacy-Patcher/POST-INSTALL.html).
- [README RestrictEvents](https://github.com/acidanthera/RestrictEvents/blob/master/README.md) pour `revpatch=sbvmm`.
- [Compatibilité itlwm](https://openintelwireless.github.io/itlwm/Compat.html) et [compatibilité Bluetooth](https://openintelwireless.github.io/IntelBluetoothFirmware/Compat.html).
- [laobamac/itlwm](https://github.com/laobamac/itlwm) pour les builds Airport Sequoia et Tahoe, et la [note AirportItlwm Sequoia de 5T33Z0](https://github.com/5T33Z0/OCLP4Hackintosh/blob/main/Enable_Features/AirportItllwm_Sequoia.md) pour expliquer pourquoi le kext officiel s'arrête à Sonoma.
- Les rapports communautaires du tableau ci-dessus. Leurs binaires et le texte de leurs README ne sont pas repris.

## Licence

MIT pour les fichiers propres à ce dépôt. Voir `LICENSE` et `THIRD-PARTY-NOTICES.md` avant de redistribuer une archive construite. VoodooPS2 est en APSL-2.0. itlwm, le fork laobamac et BlueToolFixup de BrcmPatchRAM sont en GPL-2.0. VoodooI2C et IntelBluetoothFirmware sont en GPL-3.0. ECEnabler et le kext USBToolBox n'avaient pas de fichier de licence le 2026-10-26.
