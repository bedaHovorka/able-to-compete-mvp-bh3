import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, MoreVertical } from 'lucide-react'
import { boards, lists, cards } from '../lib/api'

export default function TaskBoard() {
  const queryClient = useQueryClient()
  const [selectedBoard, setSelectedBoard] = useState<string | null>(null)
  const [newBoardName, setNewBoardName] = useState('')

  const { data: boardsList } = useQuery({
    queryKey: ['boards'],
    queryFn: () => boards.list().then((res) => res.data),
  })

  const { data: boardDetail } = useQuery({
    queryKey: ['board', selectedBoard],
    queryFn: () => boards.get(selectedBoard!).then((res) => res.data),
    enabled: !!selectedBoard,
  })

  const createBoardMutation = useMutation({
    mutationFn: (name: string) => boards.create({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
      setNewBoardName('')
    },
  })

  const createListMutation = useMutation({
    mutationFn: (data: { boardId: string; name: string }) =>
      lists.create(data.boardId, { name: data.name, position: 0 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', selectedBoard] })
    },
  })

  const createCardMutation = useMutation({
    mutationFn: (data: { listId: string; title: string }) =>
      cards.create(data.listId, { title: data.title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', selectedBoard] })
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Task Boards</h1>

        <div className="flex space-x-2">
          <input
            type="text"
            placeholder="New board name"
            value={newBoardName}
            onChange={(e) => setNewBoardName(e.target.value)}
            className="rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          />
          <button
            onClick={() => createBoardMutation.mutate(newBoardName)}
            disabled={!newBoardName}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Board
          </button>
        </div>
      </div>

      {/* Board List */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {boardsList?.map((board: any) => (
          <div
            key={board.id}
            onClick={() => setSelectedBoard(board.id)}
            className={`bg-white p-6 rounded-lg shadow cursor-pointer hover:shadow-md transition-shadow ${
              selectedBoard === board.id ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <h3 className="text-lg font-medium text-gray-900">{board.name}</h3>
            {board.description && (
              <p className="mt-1 text-sm text-gray-500">{board.description}</p>
            )}
          </div>
        ))}
      </div>

      {/* Board Detail */}
      {boardDetail && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-medium text-gray-900 mb-4">
            {boardDetail.name}
          </h2>

          <div className="flex space-x-4 overflow-x-auto pb-4">
            {boardDetail.lists?.map((list: any) => (
              <div
                key={list.id}
                className="flex-shrink-0 w-72 bg-gray-100 rounded-lg p-4"
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-medium text-gray-900">{list.name}</h3>
                  <button className="text-gray-400 hover:text-gray-600">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-2">
                  {list.cards?.map((card: any) => (
                    <div
                      key={card.id}
                      className="bg-white p-3 rounded shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                    >
                      <p className="text-sm text-gray-900">{card.title}</p>
                      {card.description && (
                        <p className="mt-1 text-xs text-gray-500">
                          {card.description}
                        </p>
                      )}
                    </div>
                  ))}

                  <button
                    onClick={() => {
                      const title = prompt('Card title:')
                      if (title) {
                        createCardMutation.mutate({ listId: list.id, title })
                      }
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-200 rounded"
                  >
                    + Add a card
                  </button>
                </div>
              </div>
            ))}

            <button
              onClick={() => {
                const name = prompt('List name:')
                if (name) {
                  createListMutation.mutate({ boardId: selectedBoard!, name })
                }
              }}
              className="flex-shrink-0 w-72 bg-gray-100 hover:bg-gray-200 rounded-lg p-4 text-gray-600 text-sm font-medium"
            >
              + Add another list
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
