import { useState } from 'react'

function App() {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [paperSize, setPaperSize] = useState('A4');
  const [commandType, setCommandType] = useState('ope');
  const [aValue, setAValue] = useState('');
  const [bValue, setBValue] = useState('');
  const [aMin, setAMin] = useState(1);
  const [aMax, setAMax] = useState(9);
  const [bMin, setBMin] = useState(1);
  const [bMax, setBMax] = useState(9);
  const [operators, setOperators] = useState(['add']);
  const [descend, setDescend] = useState(false);
  const [reverse, setReverse] = useState(false);
  const [shuffle, setShuffle] = useState(false);
  const [intermediate, setIntermediate] = useState(false);
  const [rows, setRows] = useState(10);
  const [columns, setColumns] = useState(2);
  const [withBottomAnswer, setWithBottomAnswer] = useState(false);
  const [page, setPage] = useState(1);
  const [merge, setMerge] = useState(false);
  const [csv, setCsv] = useState(false);
  const [debug, setDebug] = useState(false);

  const handleOperatorChange = (op) => {
    setOperators(prev =>
      prev.includes(op) ? prev.filter(item => item !== op) : [...prev, op]
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setPdfUrl(null);

    const formData = {
      paper_size: paperSize,
      command_type: commandType,
      ...(aValue && { a_value: parseInt(aValue) }),
      ...(bValue && { b_value: parseInt(bValue) }),
      a_min: parseInt(aMin),
      a_max: parseInt(aMax),
      b_min: parseInt(bMin),
      b_max: parseInt(bMax),
      operator: operators,
      descend: descend,
      reverse: reverse,
      shuffle: shuffle,
      intermediate: intermediate,
      rows: parseInt(rows),
      columns: parseInt(columns),
      with_bottom_answer: withBottomAnswer,
      page: parseInt(page),
      merge: merge,
      csv: csv,
      debug: debug,
    };

    try {
      const response = await fetch('http://127.0.0.1:5000/generate-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'PDF generation failed');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center py-10 font-sans">
      {/* Header */}
      <header className="w-full max-w-4xl bg-white shadow-md rounded-lg p-6 mb-8">
        <h1 className="text-3xl font-bold text-gray-800 text-center">100-Square Calculation Generator</h1>
      </header>

      {/* Main Content Area - Form */}
      <main className="w-full max-w-4xl bg-white shadow-md rounded-lg p-8">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">Generate Worksheet</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Paper Size */}
          <div>
            <label htmlFor="paperSize" className="block text-sm font-medium text-gray-700">Paper Size</label>
            <select
              id="paperSize"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={paperSize}
              onChange={(e) => setPaperSize(e.target.value)}
            >
              <option value="A4">A4</option>
              <option value="A3">A3</option>
              <option value="B5">B5</option>
              <option value="a4l">A4 Landscape</option>
            </select>
          </div>

          {/* Command Type */}
          <div>
            <label htmlFor="commandType" className="block text-sm font-medium text-gray-700">Command Type</label>
            <select
              id="commandType"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={commandType}
              onChange={(e) => setCommandType(e.target.value)}
            >
              <option value="ope">Operations (ope)</option>
              <option value="com">Complements (com)</option>
              <option value="100">100-Square (100)</option>
              <option value="99">Multiplication Table (99)</option>
              <option value="aBc">aBc Statement (aBc)</option>
              <option value="squ">Square Numbers (squ)</option>
              <option value="pi">Pi Multiplication (pi)</option>
            </select>
          </div>

          {/* Number Ranges / Values */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="aMin" className="block text-sm font-medium text-gray-700">A Min</label>
              <input type="number" id="aMin" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={aMin} onChange={(e) => setAMin(e.target.value)} />
            </div>
            <div>
              <label htmlFor="aMax" className="block text-sm font-medium text-gray-700">A Max</label>
              <input type="number" id="aMax" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={aMax} onChange={(e) => setAMax(e.target.value)} />
            </div>
            <div>
              <label htmlFor="bMin" className="block text-sm font-medium text-gray-700">B Min</label>
              <input type="number" id="bMin" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={bMin} onChange={(e) => setBMin(e.target.value)} />
            </div>
            <div>
              <label htmlFor="bMax" className="block text-sm font-medium text-gray-700">B Max</label>
              <input type="number" id="bMax" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={bMax} onChange={(e) => setBMax(e.target.value)} />
            </div>
            <div>
              <label htmlFor="aValue" className="block text-sm font-medium text-gray-700">A Value (for specific commands)</label>
              <input type="number" id="aValue" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={aValue} onChange={(e) => setAValue(e.target.value)} placeholder="Optional" />
            </div>
            <div>
              <label htmlFor="bValue" className="block text-sm font-medium text-gray-700">B Value (for specific commands)</label>
              <input type="number" id="bValue" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={bValue} onChange={(e) => setBValue(e.target.value)} placeholder="Optional" />
            </div>
          </div>

          {/* Operators */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Operators</label>
            <div className="mt-1 grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[ 'add', 'sub', 'mul', 'div', 'mix' ].map(op => (
                <div key={op} className="flex items-center">
                  <input
                    id={`op-${op}`}
                    type="checkbox"
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    checked={operators.includes(op)}
                    onChange={() => handleOperatorChange(op)}
                  />
                  <label htmlFor={`op-${op}`} className="ml-2 block text-sm text-gray-900">
                    {op.charAt(0).toUpperCase() + op.slice(1)}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Other Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="rows" className="block text-sm font-medium text-gray-700">Rows per page</label>
              <input type="number" id="rows" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={rows} onChange={(e) => setRows(e.target.value)} />
            </div>
            <div>
              <label htmlFor="columns" className="block text-sm font-medium text-gray-700">Columns per page</label>
              <input type="number" id="columns" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={columns} onChange={(e) => setColumns(e.target.value)} />
            </div>
            <div>
              <label htmlFor="page" className="block text-sm font-medium text-gray-700">Number of Pages</label>
              <input type="number" id="page" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" value={page} onChange={(e) => setPage(e.target.value)} />
            </div>
          </div>

          {/* Checkbox Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center">
              <input id="descend" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={descend} onChange={(e) => setDescend(e.target.checked)} />
              <label htmlFor="descend" className="ml-2 block text-sm text-gray-900">Descending Order</label>
            </div>
            <div className="flex items-center">
              <input id="reverse" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={reverse} onChange={(e) => setReverse(e.target.checked)} />
              <label htmlFor="reverse" className="ml-2 block text-sm text-gray-900">Reverse Order</label>
            </div>
            <div className="flex items-center">
              <input id="shuffle" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={shuffle} onChange={(e) => setShuffle(e.target.checked)} />
              <label htmlFor="shuffle" className="ml-2 block text-sm text-gray-900">Random Order</label>
            </div>
            <div className="flex items-center">
              <input id="intermediate" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={intermediate} onChange={(e) => setIntermediate(e.target.checked)} />
              <label htmlFor="intermediate" className="ml-2 block text-sm text-gray-900">Show Intermediate Formula</label>
            </div>
            <div className="flex items-center">
              <input id="withBottomAnswer" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={withBottomAnswer} onChange={(e) => setWithBottomAnswer(e.target.checked)} />
              <label htmlFor="withBottomAnswer" className="ml-2 block text-sm text-gray-900">Include Bottom Answer</label>
            </div>
            <div className="flex items-center">
              <input id="merge" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={merge} onChange={(e) => setMerge(e.target.checked)} />
              <label htmlFor="merge" className="ml-2 block text-sm text-gray-900">Merge Answer File</label>
            </div>
            <div className="flex items-center">
              <input id="csv" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={csv} onChange={(e) => setCsv(e.target.checked)} />
              <label htmlFor="csv" className="ml-2 block text-sm text-gray-900">Output CSV Raw Data</label>
            </div>
            <div className="flex items-center">
              <input id="debug" type="checkbox" className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" checked={debug} onChange={(e) => setDebug(e.target.checked)} />
              <label htmlFor="debug" className="ml-2 block text-sm text-gray-900">Debug Mode</label>
            </div>
          </div>

          <div className="flex justify-center pt-6">
            <button
              type="submit"
              className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              disabled={loading}
            >
              {loading ? 'Generating...' : 'Generate PDF'}
            </button>
          </div>
        </form>

        {/* Result Display */}
        {error && (
          <div className="mt-8 p-4 bg-red-100 text-red-700 rounded-md">
            Error: {error}
          </div>
        )}

        {pdfUrl && (
          <div className="mt-8">
            <h3 className="text-xl font-semibold text-gray-700 mb-4">Generated PDF:</h3>
            <a
              href={pdfUrl}
              download="generated_worksheet.pdf"
              className="inline-block px-6 py-3 bg-green-600 text-white font-semibold rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
            >
              Download PDF
            </a>
            <div className="mt-4 w-full h-96 border border-gray-300 rounded-md overflow-hidden">
              <iframe src={pdfUrl} className="w-full h-full"></iframe>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
