import * as React from "react";
import * as ReactDOM from "react-dom";
import CardData from "../CardData";
import UserData from "../UserData";
import Fragments from "../components/Fragments";
import MetaOverview from "../pages/MetaOverview";

const user = new UserData();

const render = (cardData: CardData) => {
	ReactDOM.render(
		<Fragments
			defaults={{
				archetype: 0,
				gameType: "RANKED_STANDARD",
				rankRange: "ALL",
				tab: "overview",
			}}
		>
			<MetaOverview
				cardData={cardData}
				user={user}
			/>
		</Fragments>,
		document.getElementById("meta-overview-container"),
	);
};

render(null);

new CardData().load(render);
