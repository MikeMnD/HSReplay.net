import React from "react";
import ReactDOM from "react-dom";
import CardData from "../CardData";
import UserData from "../UserData";
import DataInjector from "../components/DataInjector";
import Root from "../components/Root";
import { Consumer as AccountConsumer } from "../components/utils/hearthstone-account";
import MyPacks from "../pages/MyPacks";

UserData.create();

const render = (cardData: CardData) => {
	ReactDOM.render(
		<Root>
			<AccountConsumer>
				{({ account }) => (
					<DataInjector
						query={{
							key: "packs",
							params: {
								region: "" + (account && account.region),
								account_lo: "" + (account && account.lo),
							},
							url: "/api/v1/packs/",
						}}
						fetchCondition={
							UserData.hasFeature("packs") && !!account
						}
					>
						{({ packs }) => (
							<MyPacks packs={packs} cardData={cardData} />
						)}
					</DataInjector>
				)}
			</AccountConsumer>
		</Root>,
		document.getElementById("my_packs-container"),
	);
};

render(null);

new CardData().load(render);
