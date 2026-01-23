import { DecoderPage } from '@/app/components/DecoderPage';
import { FormatterPage } from '@/app/components/FormatterPage';
import { RegexPage } from '@/app/components/RegexPage';
import { ScriptPage } from '@/app/components/ScriptPage';
import { SettingsPage } from '@/app/components/SettingsPage';
import { KeyReconstructPage } from '@/app/components/KeyReconstructPage';

interface MainContentProps {
  activeTab: string;
}

export function MainContent({ activeTab }: MainContentProps) {
  const renderContent = () => {
    switch (activeTab) {
      case 'decoder':
        return <DecoderPage />;
      case 'formatter':
        return <FormatterPage />;
      case 'regex':
        return <RegexPage />;
      case 'script':
        return <ScriptPage />;
      case 'keyreconstruct':
        return <KeyReconstructPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DecoderPage />;
    }
  };

  const isFullHeightPage = activeTab === 'decoder' || activeTab === 'keyreconstruct' || activeTab === 'script';

  return (
    <main className="flex-1 h-full overflow-auto relative z-10">
      {isFullHeightPage ? (
        <div className="h-full overflow-hidden">
          {renderContent()}
        </div>
      ) : (
        <div className="min-h-full p-10">
          {renderContent()}
        </div>
      )}
    </main>
  );
}