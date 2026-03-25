import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import debounce from 'lodash.debounce'

interface Subsidy {
    id: number
    title: string
    description: string
    region: string
    prefecture: string
    city: string
    organization: string
    status: string
    start_date: string
    end_date: string
    amount: string
    subsidy_rate: string
    purpose: string
    eligible_expenses: string
    eligible_entities: string
    official_url: string
    tags: string[]
    note: string
    created_at: string
    updated_at: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const API_KEY = import.meta.env.VITE_API_KEY || 'changeme'

export default function SubsidyDetail() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const [subsidy, setSubsidy] = useState<Subsidy | null>(null)
    const [loading, setLoading] = useState(true)
    const [note, setNote] = useState('')
    const [saving, setSaving] = useState(false)
    const [lastSaved, setLastSaved] = useState<Date | null>(null)
    // 編集中フラグ：定期リフレッシュによるノート上書きを防ぐ
    const isDirtyRef = useRef(false)

    useEffect(() => {
        fetchSubsidy(true)
        const interval = setInterval(() => fetchSubsidy(false), 10000)
        return () => clearInterval(interval)
    }, [id])

    const fetchSubsidy = async (isInitial: boolean) => {
        try {
            const response = await axios.get(`${API_BASE}/api/subsidies/${id}`)
            setSubsidy(response.data)
            // 初回ロードか、編集中でない場合のみノートを更新
            if (isInitial || !isDirtyRef.current) {
                setNote(response.data.note || '')
            }
        } catch (error) {
            console.error('Failed to fetch subsidy:', error)
        } finally {
            setLoading(false)
        }
    }

    const saveNote = useCallback(
        debounce(async (content: string) => {
            if (!id) return
            setSaving(true)
            try {
                await axios.put(
                    `${API_BASE}/api/subsidies/${id}/note`,
                    { note: content },
                    { headers: { 'X-API-Key': API_KEY } }
                )
                setLastSaved(new Date())
                isDirtyRef.current = false
            } catch (error) {
                console.error('Failed to save note:', error)
            } finally {
                setSaving(false)
            }
        }, 1000),
        [id]
    )

    const handleNoteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newNote = e.target.value
        setNote(newNote)
        isDirtyRef.current = true
        saveNote(newNote)
    }

    const isExpired = (endDate: string) => {
        if (!endDate) return false
        return new Date(endDate) < new Date()
    }

    if (loading) {
        return (
            <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                <p className="mt-4 text-gray-600">読み込み中...</p>
            </div>
        )
    }

    if (!subsidy) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500">補助金情報が見つかりませんでした</p>
                <button onClick={() => navigate(-1)} className="mt-4 inline-block text-blue-600 hover:text-blue-800">
                    ← 一覧に戻る
                </button>
            </div>
        )
    }

    return (
        <div>
            <div className="mb-6">
                <button onClick={() => navigate(-1)} className="text-blue-600 hover:text-blue-800">
                    ← 一覧に戻る
                </button>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className={`p-6 ${isExpired(subsidy.end_date) ? 'bg-red-50' : 'bg-blue-50'}`}>
                    <div className="flex flex-wrap justify-between items-start gap-4 mb-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800 mb-2">{subsidy.title}</h1>
                            <p className="text-gray-600">{subsidy.description}</p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            <span className={`px-4 py-2 rounded-full text-sm font-medium ${subsidy.status === '公募中' ? 'bg-green-100 text-green-800' :
                                    subsidy.status === '終了' ? 'bg-red-100 text-red-800' :
                                        'bg-gray-100 text-gray-800'
                                }`}>
                                {subsidy.status || '情報なし'}
                            </span>
                            {isExpired(subsidy.end_date) && (
                                <span className="px-4 py-2 rounded-full text-sm font-medium bg-red-100 text-red-800">
                                    期限切れ
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <h2 className="text-xl font-bold text-gray-800 mb-4">基本情報</h2>
                            <div className="space-y-4">
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">地域</h3>
                                    <p className="text-gray-900">
                                        {subsidy.prefecture || subsidy.region || '未設定'}
                                        {subsidy.city ? ` ${subsidy.city}` : ''}
                                    </p>
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">実施機関</h3>
                                    <p className="text-gray-900">{subsidy.organization || '未設定'}</p>
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">申請期間</h3>
                                    <p className="text-gray-900">
                                        {subsidy.start_date ? format(new Date(subsidy.start_date), 'yyyy年MM月dd日', { locale: ja }) : '未設定'}
                                        {' 〜 '}
                                        {subsidy.end_date ? (
                                            <span className={isExpired(subsidy.end_date) ? 'text-red-600' : ''}>
                                                {format(new Date(subsidy.end_date), 'yyyy年MM月dd日', { locale: ja })}
                                            </span>
                                        ) : '未設定'}
                                    </p>
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">上限金額・助成額</h3>
                                    <p className="text-gray-900">{subsidy.amount || '未設定'}</p>
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">補助率</h3>
                                    <p className="text-gray-900">{subsidy.subsidy_rate || '未設定'}</p>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h2 className="text-xl font-bold text-gray-800 mb-4">詳細情報</h2>
                            <div className="space-y-4">
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">目的</h3>
                                    <p className="text-gray-900">{subsidy.purpose || '未設定'}</p>
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">対象経費</h3>
                                    <p className="text-gray-900">{subsidy.eligible_expenses || '未設定'}</p>
                                </div>
                                <div>
                                    <h3 className="font-medium text-gray-700 mb-1">対象事業者</h3>
                                    <p className="text-gray-900">{subsidy.eligible_entities || '未設定'}</p>
                                </div>
                                {subsidy.tags && subsidy.tags.length > 0 && (
                                    <div>
                                        <h3 className="font-medium text-gray-700 mb-1">関連タグ</h3>
                                        <div className="flex flex-wrap gap-2">
                                            {subsidy.tags.map((tag, index) => (
                                                <span key={index} className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {subsidy.official_url && (
                                    <div>
                                        <h3 className="font-medium text-gray-700 mb-1">公式公募ページ</h3>
                                        <a
                                            href={subsidy.official_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:text-blue-800 break-all"
                                        >
                                            {subsidy.official_url}
                                        </a>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 pt-8 border-t border-gray-200">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">共有メモ</h2>
                        <div className="mb-4">
                            <textarea
                                value={note}
                                onChange={handleNoteChange}
                                rows={4}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="この補助金に関するメモを共有できます（自動保存）"
                            />
                            <div className="flex justify-between items-center mt-2">
                                <div className="text-sm text-gray-500">
                                    {saving ? '保存中...' : lastSaved ? `最終保存: ${format(lastSaved, 'HH:mm:ss')}` : '変更は自動保存されます'}
                                </div>
                                <div className="text-sm text-gray-500">
                                    他のユーザーも編集可能です（10秒ごとに更新）
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 pt-8 border-t border-gray-200 text-sm text-gray-500">
                        <p>最終更新: {format(new Date(subsidy.updated_at), 'yyyy年MM月dd日 HH:mm:ss', { locale: ja })}</p>
                    </div>
                </div>
            </div>
        </div>
    )
}