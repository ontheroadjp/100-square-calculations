import { useTranslation } from 'react-i18next';
import './App.css';
import GradeDrills from './GradeDrills';

function App() {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>{t('app_title')}</h1>
        <div className="lang-switcher">
          <button
            onClick={() => changeLanguage('en')}
            className={i18n.language === 'en' ? 'active' : ''}
          >
            English
          </button>
          <button
            onClick={() => changeLanguage('ja')}
            className={i18n.language === 'ja' ? 'active' : ''}
          >
            日本語
          </button>
        </div>
      </header>

      <main className="main-content">
        <GradeDrills />
      </main>
    </div>
  );
}

export default App;
