# संपूर्ण हिंदी पाठक बनाना

आवश्यकताएँ: TeX Live जिसमें `latexmk`, XeLaTeX, BibTeX और Noto Serif
Devanagari उपलब्ध हों। Repository root से PowerShell में चलाएँ:

```powershell
./build/build.ps1
```

आउटपुट `build/out/open-logic-complete-hi-build.pdf` होगा। जमी हुई bibliography
के लिए script `BIBINPUTS` और `BSTINPUTS` को केवल command के दौरान सेट करती है।
