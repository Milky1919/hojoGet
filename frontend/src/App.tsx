import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import SubsidyList from './pages/SubsidyList'
import SubsidyDetail from './pages/SubsidyDetail'

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-gray-50">
                <header className="bg-white shadow">
                    <div className="container mx-auto px-4 py-4">
                        <div className="flex justify-between items-center">
                            <h1 className="text-2xl font-bold text-blue-800">
                                <Link to="/">補助金ポータル</Link>
                            </h1>
                            <nav>
                                <Link to="/" className="text-gray-700 hover:text-blue-600 px-3 py-2">
                                    一覧
                                </Link>
                            </nav>
                        </div>
                    </div>
                </header>
                <main className="container mx-auto px-4 py-8">
                    <Routes>
                        <Route path="/" element={<SubsidyList />} />
                        <Route path="/subsidies/:id" element={<SubsidyDetail />} />
                    </Routes>
                </main>
                <footer className="bg-gray-800 text-white py-6 mt-12">
                    <div className="container mx-auto px-4 text-center">
                        <p>© 2024 補助金ポータル - IT・ものづくり系補助金情報</p>
                    </div>
                </footer>
            </div>
        </Router>
    )
}

export default App