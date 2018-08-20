all:
	elm-make src/Main.elm --warn --output ../src/program/static/js/elm_based_schedule.js

debug:
	elm-make src/Main.elm --debug --warn --output ../src/program/static/js/elm_based_schedule.js

docker:
	docker image build \
			-f Dockerfile \
			-t "bornhack-elm" .
	cd .. && docker run --init \
			-v $$PWD:/bornhack \
			"bornhack-elm" \

clean:
	docker container prune -f
	docker image prune -f

