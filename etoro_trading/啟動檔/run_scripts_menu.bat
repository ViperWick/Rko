@echo off
chcp 65001 >nul
set "PATH=C:\Users\User\AppData\Local\Programs\Python\Launcher;C:\Users\User\AppData\Local\Programs\Python\Python313;C:\Users\User\miniconda3;%PATH%"
cd /d "%~dp0\..\.."

:menu
cls
echo ============================================================
echo   eToro 輔助腳本選單  精簡版
echo   等同: py -m etoro_trading.scripts
echo   說明: 本資料夾 README_啟動檔.md
echo   僅 Word 匯出請打: py -m etoro_trading.scripts export-integrated --word
echo ============================================================
echo.
echo  [帳戶／持倉 — 多數需 etoro_trading 目錄內 .env]
echo    1  今日總結 Markdown
echo    2  匯出 portfolio_summary.json
echo    3  今日組合與市場表現報告
echo    4  持倉與止盈候選清單
echo    5  持倉昨日漲跌與建議  建議先執行 2
echo    6  除錯 API 持倉原始結構
echo.
echo  [研究／匯出]
echo    7  抓取基本面到 fundamentals.json
echo    8  簡易估值  需先執行 7
echo    9  標的相關性矩陣  eToro K線
echo   10  投資組合風險評分
echo   11  整合總表  僅 Excel
echo   12  整合總表  Excel 加 Word 一併匯出
echo   13  量子板塊觀察清單 Excel
echo   14  依 JSON 更新持倉分析 md  需先執行 2
echo.
echo  [資料建置／其他]
echo   15  建立或擴充 instrument_ids.json  API 較慢
echo   16  從持倉挑 5 檔觀察
echo   17  防務板塊 eToro 解析
echo   18  Alpha Portfolios 追蹤
echo   19  散戶 vs AI 模擬示範
echo   20  Ollama 摘要最新自動化 log  需本機 Ollama
echo.
echo    H  顯示完整說明  同 --help
echo    0  結束
echo.
set /p "CHOICE=請輸入選項後 Enter: "

if "%CHOICE%"=="0" exit /b 0
if /i "%CHOICE%"=="H" goto help

if "%CHOICE%"=="1" py -m etoro_trading.scripts today-summary & goto done
if "%CHOICE%"=="2" py -m etoro_trading.scripts export-portfolio & goto done
if "%CHOICE%"=="3" py -m etoro_trading.scripts daily-performance & goto done
if "%CHOICE%"=="4" py -m etoro_trading.scripts list-positions-tp & goto done
if "%CHOICE%"=="5" py -m etoro_trading.scripts check-yesterday & goto done
if "%CHOICE%"=="6" py -m etoro_trading.scripts debug-positions & goto done
if "%CHOICE%"=="7" py -m etoro_trading.scripts fetch-fundamentals & goto done
if "%CHOICE%"=="8" py -m etoro_trading.scripts calc-valuation & goto done
if "%CHOICE%"=="9" py -m etoro_trading.scripts calc-correlation & goto done
if "%CHOICE%"=="10" py -m etoro_trading.scripts calc-risk & goto done
if "%CHOICE%"=="11" py -m etoro_trading.scripts export-integrated & goto done
if "%CHOICE%"=="12" py -m etoro_trading.scripts export-integrated --all & goto done
if "%CHOICE%"=="13" py -m etoro_trading.scripts quantum-xlsx & goto done
if "%CHOICE%"=="14" py -m etoro_trading.scripts generate-analysis & goto done
if "%CHOICE%"=="15" py -m etoro_trading.scripts build-instrument-map & goto done
if "%CHOICE%"=="16" py -m etoro_trading.scripts pick-watchlist & goto done
if "%CHOICE%"=="17" py -m etoro_trading.scripts build-defense & goto done
if "%CHOICE%"=="18" py -m etoro_trading.scripts track-alpha & goto done
if "%CHOICE%"=="19" py -m etoro_trading.scripts simulate-retail & goto done
if "%CHOICE%"=="20" py -m etoro_trading.scripts ollama-summarize & goto done

echo 無效選項，請重試。
timeout /t 2 >nul
goto menu

:help
py -m etoro_trading.scripts --help
goto done

:done
echo.
pause
goto menu
