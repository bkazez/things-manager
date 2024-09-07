on todoWithID(todoID)
	tell application "Things3"
		set activeTodos to (to dos)
		set completedTodos to ((to dos) of list "Logbook")
		set allTodos to activeTodos & completedTodos

		repeat with todo in allTodos
			if id of todo is todoID then
				return todo
			end if
		end repeat
	end tell
end todoWithID
