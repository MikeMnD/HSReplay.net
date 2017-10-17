import * as React from "react";
import * as ReactDOM from "react-dom";
import CardData from "../CardData";
import UserData from "../UserData";
import Fragments from "../components/Fragments";
import Discover from "../pages/Discover";
import HSReplayNetProvider from "../components/HSReplayNetProvider";

const container = document.getElementById("discover-container");

const render = (cardData: CardData) => {
	ReactDOM.render(
		<HSReplayNetProvider>
			<Fragments
				defaults={{
					dataset: "live",
					format: "FT_STANDARD",
					playerClass: "DRUID",
					sampleSize: UserData.getSetting("discover-samplesize") || "250",
					tab: "decks",
					zoomEnabled: "",
				}}
				immutable={!UserData.hasFeature("archetype-training") ? ["dataset", "format"] : null}
			>
				<Discover
					cardData={cardData}
				/>
			</Fragments>
		</HSReplayNetProvider>,
		container,
	);
};

render(null);

new CardData().load(render);
