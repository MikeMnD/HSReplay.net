import * as React from "react";
import {GameReplay, CardArtProps, ImageProps, GlobalGamePlayer} from "../interfaces";
import GameHistorySearch from "./GameHistorySearch";
import GameHistoryModeFilter from "./GameHistoryModeFilter";
import GameHistoryFormatFilter from "./GameHistoryFormatFilter"
import GameHistoryList from "./GameHistoryList";
import Pager from "./Pager";
import {parseQuery, toQueryString} from "../QueryParser"
import {formatMatch, modeMatch, nameMatch} from "../GameFilters"


interface MyReplaysProps extends ImageProps, CardArtProps, React.ClassAttributes<MyReplays> {
	username: string;
}

interface MyReplaysState {
	working?: boolean;
	queryMap?: Map<string, string>;
	gamesPages?: Map<number, GameReplay[]>;
	count?: number;
	next?: string,
	receivedPages?: number;
	currentLocalPage?: number;
	pageSize?: number;
}

export default class MyReplays extends React.Component<MyReplaysProps, MyReplaysState> {

	constructor(props: MyReplaysProps, context: any) {
		super(props, context);
		this.state = {
			working: true,
			queryMap: parseQuery(document.location.hash.substr(1)),
			gamesPages: new Map<number, GameReplay[]>(),
			count: 0,
			next: null,
			receivedPages: 0,
			currentLocalPage: 0,
			pageSize: 1
		};
		this.query("/api/v1/games/");
	}

	protected query(url: string) {
		this.setState({
			working: true
		});
		$.getJSON(url, {username: this.props.username}, (data) => {
			let games = [];
			if (data.count) {
				games = data.results;
				if (!this.state.gamesPages.has(this.state.receivedPages)) {
					this.state.gamesPages = this.state.gamesPages.set(this.state.receivedPages, games);
					this.state.receivedPages++;
					if(games.length > this.state.pageSize) {
						this.state.pageSize = games.length;
					}
				}
			}
			this.setState({
				working: false,
				count: data.count,
				next: data.next
			});
		});
	}

	componentDidUpdate(prevProps: MyReplaysProps, prevState: MyReplaysState, prevContext: any): void {
		location.replace("#" + toQueryString(this.state.queryMap));
	}

	filterGames(input: GameReplay[]): GameReplay[] {
		let games = input;
		if (this.state.queryMap.size > 0) {
			var name = this.state.queryMap.get("name");
			var mode = this.state.queryMap.get("mode");
			var format = this.state.queryMap.get("format");
			games = games.filter(game => {
				if(name && !nameMatch(game, name.toLowerCase())) {
					return false;
				}
				if(mode && !modeMatch(game, mode)) {
					return false;
				}
				if(format && !formatMatch(game, format, mode)) {
					return false;
				}
				return true;
			});
		}
		return games;
	}

	render(): JSX.Element {
		let games = [];
		let hasFilters = false;
		this.state.queryMap.forEach(v => hasFilters = hasFilters || !!v && v.length > 0);

		let page = 0;
		if(this.state.gamesPages.has(page)) {
			games = this.filterGames(this.state.gamesPages.get(page));
			//we load one more than we need so we know whether there is next page
			while (games.length < (this.state.pageSize * (this.state.currentLocalPage + 1) + 1)) {
				page++;
				if (!this.state.gamesPages.has(page)) {
					if (this.state.next && !this.state.working && (hasFilters || page == this.state.currentLocalPage)) {
						this.query(this.state.next);
					}
					break;
				}
				games = games.concat(this.filterGames(this.state.gamesPages.get(page)));
			}
			//slice off everything before the currentLocalPage
			games = games.slice(this.state.pageSize * (this.state.currentLocalPage));
		}

		let hasNext = !hasFilters && this.state.next || games.length > this.state.pageSize;
		if (hasNext) {
			games = games.slice(0, this.state.pageSize);
		}

		let content = null;
		if (games.length) {
			content =  <GameHistoryList
				image={this.props.image}
				cardArt={this.props.cardArt}
				games={games}
			/>;
		}
		else {
			let message = null;
			if (this.state.working) {
				message = <p>Loading replays…</p>;
			}
			else {
				message = <div>
					<h2>No replay found</h2>
					{!!this.state.queryMap ? <p>
						<a href="#"
						   onClick={(e) => {e.preventDefault(); this.setState({queryMap: new Map<string, string>()})}}>Reset search</a>
					</p> : null}
				</div>;
			}
			content = <div className="list-message">{message}</div>;
		}

		let next = hasNext && !this.state.working ? () => {
			this.setState({currentLocalPage: this.state.currentLocalPage + 1});
		} : null;

		let previous = this.state.currentLocalPage > 0 ? () => {
			this.setState({currentLocalPage: this.state.currentLocalPage - 1});
		} : null;

		return (
			<div>
				<div className="row" id="replay-search">
					<div className="col-md-12 col-sm-12 col-xs-12 text-right">
						<br className="visible-xs-inline"/>
						<Pager next={next} previous={previous}/>
					</div>
					<div className="col-md-3 col-sm-4 col-xs-12">
						<GameHistorySearch
							query={this.state.queryMap.get("name")}
							setQuery={(value: string) => this.setState({queryMap: this.state.queryMap.set("name", value), currentLocalPage: 0})}
						/>
					</div>
					<div className="col-md-3 col-sm-4 col-xs-12">
						<GameHistoryModeFilter
							selected={this.state.queryMap.get("mode")}
							setQuery={(value: string) => this.setState({queryMap: this.state.queryMap.set("mode", value), currentLocalPage: 0})}
						/>
					</div>
					<div className="col-md-3 col-sm-4 col-xs-12">
						<GameHistoryFormatFilter
							selected={this.state.queryMap.get("format")}
							setQuery={(value: string) => this.setState({queryMap: this.state.queryMap.set("format", value), currentLocalPage: 0})}
						/>
					</div>
				</div>
				<div className="clearfix"/>
				{content}
				<div className="pull-right">
					<Pager next={next} previous={previous}/>
				</div>
			</div>
		);
	}
}
