import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'

interface Subsidy {
    id: number
    title: string
    description: string
    region: string
    status: string
    end_date: string
    amount: string
    subsidy_rate: string
    note: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function SubsidyList() {
    const [subsidies, setSubsidies] = useState<Subsidy[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [region, setRegion] = useState('')
    const [includeExpired, setIncludeExpired] = useState(false)
    const [regions, setRegions] = useState<string[]>([])

    useEffect(() => {
        fetchSubsidies()
    }, [search, region, includeExpired])

    const fetchSubsidies = async () => {
        setLoading(true)
        try {
            const params = new URLSearchParams()
            if (search) params.append('q', search)
            if (region) params.append('region', region)
            if (includeExpired) params.append('include_expired', 'true')

            const response = await axios.get(`${API_BASE}/api/subsidies?${params}`)
            setSubsidies(response.data)

            // 地域リストを抽出
            const uniqueRegions = Array.from(new Set(response.data.map((s: Subsidy) => s.region).filter(Boolean)))
            setRegions(uniqueRegions as string[])
        } catch (error) {
            console.error('Failed to fetch subsidies:', error)
        } finally {
            setLoading(false)
        }
    }

    const isExpired = (endDate: string) => {
        if (!endDate) return false
        return new Date(endDate) < new Date()
    }

    return (
        <div>
            <div className="mb-8">
                <h2 className="text-3xl font-bold text-gray-800 mb-4">補助金一覧</h2>
                <p className="text-gray-600">IT・ものづくり系の補助金情報を掲載しています</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6 mb-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">キーワード検索</label>
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="タイトル、説明、地域など"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">地域</label>
                        <select
                            value={region}
                            onChange={(e) => setRegion(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="">すべて</option>
                            {regions.map((r) => (
                                <option key={r} value={r}>{r}</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex items-end">
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={includeExpired}
                                onChange={(e) => setIncludeExpired(e.target.checked)}
                                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-700">期限切れを含む</span>
                        </label>
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                    <p className="mt-4 text-gray-600">読み込み中...</p>
                </div>
            ) : subsidies.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                    <p className="text-gray-500">該当する補助金が見つかりませんでした</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {subsidies.map((subsidy) => (
                        <div
                            key={subsidy.id}
                            className={`bg-white rounded-lg shadow hover:shadow-lg transition-shadow duration-200 ${isExpired(subsidy.end_date) ? 'opacity-70 border-l-4 border-red-500' : ''
                                }`}
                        >
                            <div className="p-6">
                                <div className="flex justify-between items-start mb-3">
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${subsidy.status === '公募中' ? 'bg-green-100 text-green-800' :
                                            subsidy.status === '終了' ? 'bg-red-100 text-red-800' :
                                                'bg-gray-100 text-gray-800'
                                        }`}>
                                        {subsidy.status || '情報なし'}
                                    </span>
                                    {isExpired(subsidy.end_date) && (
                                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                            期限切れ
                                        </span>
                                    )}
                                </div>
                                <h3 className="text-xl font-bold text-gray-800 mb-2 line-clamp-2">
                                    <Link to={`/subsidies/${subsidy.id}`} className="hover:text-blue-600">
                                        {subsidy.title}
                                    </Link>
                                </h3>
                                <p className="text-gray-600 mb-4 line-clamp-3">{subsidy.description}</p>
                                <div className="space-y-2 mb-4">
                                    <div className="flex items-center text-sm text-gray-700">
                                        <span className="font-medium mr-2">地域:</span>
                                        <span>{subsidy.region || '未設定'}</span>
                                    </div>
                                    <div className="flex items-center text-sm text-gray-700">
                                        <span className="font-medium mr-2">金額:</span>
                                        <span>{subsidy.amount || '未設定'}</span>
                                    </div>
                                    {subsidy.end_date && (
                                        <div className="flex items-center text-sm text-gray-700">
                                            <span className="font-medium mr-2">申請期限:</span>
                                            <span className={isExpired(subsidy.end_date) ? 'text-red-600' : ''}>
                                                {format(new Date(subsidy.end_date), 'yyyy年MM月dd日', { locale: ja })}
                                            </span>
                                        </div>
                                    )}
                                </div>
                                <div className="flex justify-between items-center">
                                    <Link
                                        to={`/subsidies/${subsidy.id}`}
                                        className="text-blue-600 hover:text-blue-800 font-medium"
                                    >
                                        詳細を見る →
                                    </Link>
                                    {subsidy.note && (
                                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                            メモあり
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}